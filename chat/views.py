from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from users.models import CustomUser
from .messenger import pusher_client
from .models import Message, Group, GroupMessage
import hashlib
from django.utils import timezone

@api_view(['POST'])
@permission_classes([AllowAny]) # Change to IsAuthenticated after testing or when the frontend is ready
def send_message(request):
    """
    Send a message to a user
    """
    try:
        # Get the sender and recipient
        sender_username = request.data.get('sender')
        recipient_username = request.data.get('recipient')
        message_text = request.data.get('message')
        timestamp = timezone.now()

        if len(message_text) > 256:
            return Response({"error": "Message too long upto 200 chars are allowed"}, status=status.HTTP_400_BAD_REQUEST)

        # verify that the sender and recipient exist
        sender = CustomUser.objects.get(username=sender_username)
        recipient = CustomUser.objects.get(username=recipient_username)

        if not sender or not recipient:
            return Response({"error": "Invalid sender or recipient"}, status=status.HTTP_400_BAD_REQUEST)

        # Send the message
        pusher_client.trigger(
            f'{recipient_username}',
            f'{sender_username}',
            {
                'sender': sender_username,
                'message': message_text,
                'timestamp': timestamp.isoformat()
            },
        )

        # Save the message
        message_object = Message.objects.create(sender=sender, recipient=recipient, message=message_text)
        Message.save(message_object)

        messages = Message.objects.filter(sender=sender, recipient=recipient) | Message.objects.filter(sender=recipient, recipient=sender)
        messages = messages.order_by('-timestamp')

        if messages.count() > 20:
            messages[20:].delete()
        
        return Response({"message": "Message sent"}, status=status.HTTP_200_OK)
    
    except CustomUser.DoesNotExist:
        return Response({"error": "Invalid sender or recipient"}, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        print(e)
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

@api_view(['POST'])
@permission_classes([AllowAny])
def send_group_message(request):
    """
    Send a message to a group
    """
    try:
        # Get the sender and group
        sender_username = request.data.get('sender')
        group_username = request.data.get('group')
        message = request.data.get('message')
        timestamp = timezone.now()

        if len(message) > 256:
            return Response({"error": "Message too long upto 200 chars are allowed"}, status=status.HTTP_400_BAD_REQUEST)

        # verify that the sender and group exist
        sender = CustomUser.objects.get(username=sender_username)
        group = Group.objects.get(username=group_username)

        if not sender or not group:
            return Response({"error": "Invalid sender or group"}, status=status.HTTP_400_BAD_REQUEST)
        
        # get the group members
        members = group.members.all()

        # Send the message to each member
        for member in members:

            if member.username == sender_username:
                continue

            pusher_client.trigger(
                f'{member.username}',
                f'{group_username}',
                {
                    'sender': sender_username,
                    'message': message,
                    'timestamp': timestamp.isoformat()
                },
            )

        # Save the message
        message = GroupMessage.objects.create(sender=sender, group=group, message=message, timestamp=timestamp)
        GroupMessage.save(message)

        messages = GroupMessage.objects.filter(group=group)
        messages = messages.order_by('-timestamp')

        if messages.count() > 20:
            messages[20:].delete()
        
        return Response({"message": "Message sent"}, status=status.HTTP_200_OK)
    
    except CustomUser.DoesNotExist:
        return Response({"error": "Invalid sender or group"}, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

@api_view(['GET'])
@permission_classes([AllowAny])
def get_messages(request):
    """
    Get messages between two users
    """
    try:
        # Get the sender and recipient
        sender_username = request.query_params.get('sender')
        recipient_username = request.query_params.get('recipient')

        # verify that the sender and recipient exist
        sender = CustomUser.objects.get(username=sender_username)
        recipient = CustomUser.objects.get(username=recipient_username)

        if not sender or not recipient:
            return Response({"error": "Invalid sender or recipient"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get the messages
        messages = Message.objects.filter(sender=sender, recipient=recipient) | Message.objects.filter(sender=recipient, recipient=sender)
        message_list = []

        messages = messages.order_by('-timestamp')[:20]

        for message in messages:
            message_list.append({
                "sender": message.sender.username,
                "recipient": message.recipient.username,
                "message": message.message,
                "timestamp": message.timestamp
            })

        return Response(message_list, status=status.HTTP_200_OK)
    
    except CustomUser.DoesNotExist:
        return Response({"error": "Invalid sender or recipient"}, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

@api_view(['GET'])
@permission_classes([AllowAny])
def get_group_messages(request):
    """
    Get messages in a group
    """
    try:
        # Get the group
        group_username = request.query_params.get('group')

        # verify that the group exists
        group = Group.objects.get(username=group_username)

        if not group:
            return Response({"error": "Invalid group"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get the messages
        messages = GroupMessage.objects.filter(group=group)
        message_list = []

        messages = messages.order_by('-timestamp')[:20]

        for message in messages:
            message_list.append({
                "sender": message.sender.username,
                "group": message.group.username,
                "message": message.message,
                "timestamp": message.timestamp
            })

        return Response(message_list, status=status.HTTP_200_OK)
    
    except Group.DoesNotExist:
        return Response({"error": "Invalid group"}, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
@api_view(['POST'])
@permission_classes([AllowAny])
def create_group(request):
    """
    Create a group
    """
    try:
        group_name = request.data.get('name')
        members_usernames = request.data.get('members')

        if not isinstance(members_usernames, list):
            return Response({"error": "Members must be a list of usernames"}, status=status.HTTP_400_BAD_REQUEST)
        
        if len(members_usernames) < 1 or len(members_usernames) > 20:
            return Response({"error": "Members must be between 1 and 20"}, status=status.HTTP_400_BAD_REQUEST)

        members = CustomUser.objects.filter(username__in=members_usernames)

        if not members:
            return Response({"error": "Invalid member"}, status=status.HTTP_400_BAD_REQUEST)
        
        base_string = group_name + "".join(members_usernames)
        username = hashlib.sha256(base_string.encode()).hexdigest()[:12]

        if Group.objects.filter(username=username).exists():
            return Response({"error": "Group already exists with same name and members"}, status=status.HTTP_400_BAD_REQUEST)

        group = Group.objects.create(username=username, name=group_name)
        group.members.set(members)
        group.save()

        return Response({"message": "Group created", "username": f"{username}"}, status=status.HTTP_201_CREATED)
    
    except CustomUser.DoesNotExist:
        return Response({"error": "Invalid member"}, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        print(e)
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

@api_view(['POST'])
@permission_classes([AllowAny])
def add_group_members(request):

    try:
        group_username = request.data.get('group_username')
        members_usernames = request.data.get('members_usernames')

        if isinstance(members_usernames, list):


            # total number of members in the group should not exceed 20
            group = Group.objects.get(username=group_username)
            if group.members.count() + len(members_usernames) > 20:
                return Response({"error": "Group members should not exceed 20."}, status=status.HTTP_400_BAD_REQUEST)


            for username in members_usernames:
                member = CustomUser.objects.get(username=username)
                group = Group.objects.get(username=group_username)

                # check if member is already in the group
                if member in group.members.all():
                    return Response({"error": f"{username} is already in the group."}, status=status.HTTP_400_BAD_REQUEST)

                group.members.add(member)
            
            group.save()
            
            return Response({"message": "Members added to group successfully."}, status=status.HTTP_200_OK)
        
        else:

            return Response({"error": "Members must be a list of usernames."}, status=status.HTTP_400_BAD_REQUEST)

    except Group.DoesNotExist:
        return Response({"error": "Group not found."}, status=status.HTTP_404_NOT_FOUND)
    
    except CustomUser.DoesNotExist:
        return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
    
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

@api_view(["GET"])
@permission_classes([AllowAny])
def get_groups(requests):

    user = requests.query_params.get("user")

    groups = Group.objects.filter(members__username=user)
    group_list = []

    for group in groups:
        group_list.append({
            "name": group.name,
            "username": group.username,
            "members": [member.username for member in group.members.all()]
        })

    return Response(group_list, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([AllowAny])
def get_all_groups(requests):
    groups = Group.objects.all()
    group_list = []

    for group in groups:
        group_list.append({
            "name": group.name,
            "username": group.username,
            "members": [member.username for member in group.members.all()]
        })

    return Response(group_list, status=status.HTTP_200_OK)
    
