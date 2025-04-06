from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from users.models import CustomUser
from .messenger import pusher_client
from .models import Message, Group, GroupMessage, FileMessage, GroupFileMessage
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
        message_iv = request.data.get('iv')
        timestamp = timezone.now()

        if len(message_text) > 256:
            return Response({"error": "Message too long upto 200 chars are allowed"}, status=status.HTTP_400_BAD_REQUEST)

        # verify that the sender and recipient exist
        sender = CustomUser.objects.get(username=sender_username)
        recipient = CustomUser.objects.get(username=recipient_username)

        if not sender or not recipient:
            return Response({"error": "Invalid sender or recipient"}, status=status.HTTP_400_BAD_REQUEST)
        
        if not sender.is_verified or not recipient.is_verified:
            return Response({"error": "Sender or recipient is not verified"}, status=status.HTTP_400_BAD_REQUEST)
        
        if sender.is_suspended or recipient.is_suspended:
            return Response({"error": "Sender or recipient is suspended"}, status=status.HTTP_400_BAD_REQUEST)

        print("sent mesaage: ", message_text)

        # Send the message
        pusher_client.trigger(
            f'{recipient_username}',
            f'{sender_username}',
            {
                'sender': sender_username,
                'type': 'text',
                'message': message_text,
                'iv': message_iv,
                'timestamp': timestamp.isoformat()
            },
        )

        # Save the message
        message_object = Message.objects.create(sender=sender, recipient=recipient, message=message_text, iv=message_iv)
        Message.save(message_object)

        messages = Message.objects.filter(sender=sender, recipient=recipient) | Message.objects.filter(sender=recipient, recipient=sender)
        messages = messages.order_by('-timestamp')

        if messages.count() > 20:
            message_ids_to_delete = messages.values_list('id', flat=True)[20:]
            Message.objects.filter(id__in=message_ids_to_delete).delete()
        
        return Response({"message": "Message sent"}, status=status.HTTP_200_OK)
    
    except CustomUser.DoesNotExist:
        return Response({"error": "Invalid sender or recipient"}, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        print(e)
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def send_file(request):
    try:

        print(request.data)

        sender_username = request.data.get('sender')
        recipient_username = request.data.get('recipient')
        file = request.data.get("file")
        file_name = request.data.get("file_name")
        file_type = request.data.get("file_type")
        iv = request.data.get("iv")
        timestamp = timezone.now()

        if len(file) > 1024*1000:
            return Response({"error": "File too large"}, status=status.HTTP_400_BAD_REQUEST)

        sender = CustomUser.objects.get(username=sender_username)
        recipient = CustomUser.objects.get(username=recipient_username)
        if not sender or not recipient:
            return Response({"error": "Invalid sender or recipient"}, status=status.HTTP_400_BAD_REQUEST)
        if not sender.is_verified or not recipient.is_verified:
            return Response({"error": "Sender or recipient is not verified"}, status=status.HTTP_400_BAD_REQUEST)
        if sender.is_suspended or recipient.is_suspended:
            return Response({"error": "Sender or recipient is suspended"}, status=status.HTTP_400_BAD_REQUEST)
        
        # chunk_size = 1024*9
        # chunks = [file[i:i + chunk_size] for i in range(0, len(file), chunk_size)]

        # for i, chunk in enumerate(chunks):
        #     pusher_client.trigger(
        #         f'{recipient_username}',
        #         f'{sender_username}',
        #         {
        #             'sender': sender_username,
        #             'file_chuck': chunk,
        #             'file_name': file_name,
        #             'file_type': file_type,
        #             'chunk_index': i+1,
        #             'total_chunks': len(chunks)
        #         },
        #     )

        pusher_client.trigger(
            f'{recipient_username}',
            f'{sender_username}',
            {
                'sender': sender_username,
                'type': 'file',
                'message': 'FILE_SENT_TO_CHAT',
                'iv': iv,
                'timestamp': timestamp.isoformat()
            },
        )


        file_message = FileMessage.objects.create(sender=sender, recipient=recipient, file=file, iv=iv, filename=file_name, file_type=file_type)
        FileMessage.save(file_message)

        files = FileMessage.objects.filter(sender=sender, recipient=recipient) | FileMessage.objects.filter(sender=recipient, recipient=sender)
        files = files.order_by('-timestamp')

        if files.count() > 5:
            file_ids_to_delete = files.values_list('id', flat=True)[5:]
            FileMessage.objects.filter(id__in=file_ids_to_delete).delete()

        return Response({"message": "File sent"}, status=status.HTTP_200_OK)
    
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

        if sender.is_suspended:
            return Response({"error": "Sender is suspended"}, status=status.HTTP_400_BAD_REQUEST)

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
                    'type': 'text',
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
            message_ids_to_delete = messages.values_list('id', flat=True)[20:]
            GroupMessage.objects.filter(id__in=message_ids_to_delete).delete()
        
        return Response({"message": "Message sent"}, status=status.HTTP_200_OK)
    
    except CustomUser.DoesNotExist:
        return Response({"error": "Invalid sender or group"}, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def send_group_file(request):

    try:

        print(request.data)
        sender_username = request.data.get('sender')
        print(sender_username)
        group_username = request.data.get('group')
        file = request.data.get("file")
        file_name = request.data.get("file_name")
        file_type = request.data.get("file_type")
        iv = request.data.get("iv")
        timestamp = timezone.now()

        if len(file) > 1024*1000:
            return Response({"error": "File too large"}, status=status.HTTP_400_BAD_REQUEST)

        print(sender_username)
        sender = CustomUser.objects.get(username=sender_username)
        group = Group.objects.get(username=group_username)

        if not sender or not group:
            return Response({"error": "Invalid sender or group"}, status=status.HTTP_400_BAD_REQUEST)
        
        if sender.is_suspended:
            return Response({"error": "Sender is suspended"}, status=status.HTTP_400_BAD_REQUEST)

        # get the group members
        members = group.members.all()

        # chunk_size = 1024*9
        # chunks = [file[i:i + chunk_size] for i in range(0, len(file), chunk_size)]

        # for member in members:

        #     if member.username == sender_username:
        #         continue

        #     for i, chunk in enumerate(chunks):
        #         pusher_client.trigger(
        #             f'{member.username}',
        #             f'{group_username}',
        #             {
        #                 'sender': sender_username,
        #                 'file_chunk': chunk,
        #                 'file_name': file_name,
        #                 'file_type': file_type,
        #                 'chunk_index': i+1,
        #                 'total_chunks': len(chunks)
        #             },
        #         )

        for member in members:

            if member.username == sender_username:
                continue

            pusher_client.trigger(
                f'{member.username}',
                f'{group_username}',
                {
                    'sender': sender_username,
                    'type': 'file',
                    'message': 'FILE_SENT_TO_CHAT',
                    'iv': iv,
                    'timestamp': timestamp.isoformat()
                },
            )

        # Save the message
        message = GroupFileMessage.objects.create(sender=sender, group=group, file=file, iv=iv, filename=file_name, file_type=file_type)
        GroupFileMessage.save(message)

        messages = GroupFileMessage.objects.filter(group=group)
        messages = messages.order_by('-timestamp')

        if messages.count() > 5:
            message_ids_to_delete = messages.values_list('id', flat=True)[5:]
            GroupFileMessage.objects.filter(id__in=message_ids_to_delete).delete()
        
        return Response({"message": "File sent"}, status=status.HTTP_200_OK)
    
    except CustomUser.DoesNotExist:
        return Response({"error": "Invalid sender or group"}, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        # print(e)
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_messages(request):
    """
    Get messages between two users
    """
    try:
        sender_username = request.query_params.get('sender')
        recipient_username = request.query_params.get('recipient')

        # if request.user.username != sender_username:
        #     print(request.user.username, sender_username)
        #     return Response({"error": "User not authorized"}, status=status.HTTP_401_UNAUTHORIZED)

        sender = CustomUser.objects.get(username=sender_username)
        recipient = CustomUser.objects.get(username=recipient_username)

        if not sender or not recipient:
            return Response({"error": "Invalid sender or recipient"}, status=status.HTTP_400_BAD_REQUEST)
        
        messages = Message.objects.filter(sender=sender, recipient=recipient) | Message.objects.filter(sender=recipient, recipient=sender)
        message_list = []

        files = FileMessage.objects.filter(sender=sender, recipient=recipient) | FileMessage.objects.filter(sender=recipient, recipient=sender)

        messages = messages.order_by('-timestamp')[:20]
        files = files.order_by('-timestamp')[:5]

        for message in messages:
            message_list.append({
                "sender": message.sender.username,
                "recipient": message.recipient.username,
                "type": "text",
                "message": message.message,
                "iv": message.iv,
                "timestamp": message.timestamp
            })

        for file in files:
            message_list.append({
                "sender": file.sender.username,
                "recipient": file.recipient.username,
                "type": "file",
                "file": file.file,
                "filename": file.filename,
                "file_type": file.file_type,
                "iv": file.iv,
                "timestamp": file.timestamp
            })

        # Sort the messages by timestamp
        message_list.sort(key=lambda x: x['timestamp'], reverse=True)

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

        # Get the files
        files = GroupFileMessage.objects.filter(group=group)

        # Check if the user is a member of the group
        # if request.user not in group.members.all():
        #     return Response({"error": "User not authorized"}, status=status.HTTP_401_UNAUTHORIZED)

        messages = messages.order_by('-timestamp')[:20]
        files = files.order_by('-timestamp')[:5]

        for message in messages:
            message_list.append({
                "sender": message.sender.username,
                "group": message.group.username,
                "message": message.message,
                "timestamp": message.timestamp
            })

        for file in files:
            message_list.append({
                "sender": file.sender.username,
                "group": file.group.username,
                "file": file.file,
                "filename": file.filename,
                "file_type": file.file_type,
                "timestamp": file.timestamp
            })

        # Sort the messages by timestamp
        message_list.sort(key=lambda x: x['timestamp'], reverse=True)

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


            # total number of members in the group should not exceed 10
            group = Group.objects.get(username=group_username)
            if group.members.count() + len(members_usernames) > 10:
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

@api_view(["GET"])
@permission_classes([AllowAny])
def get_user_public_key(requests):
    try:
        username = requests.query_params.get("username")

        if not username:
            return Response({"error": "Username is required"}, status=status.HTTP_400_BAD_REQUEST)

        user = CustomUser.objects.get(username=username)

        if not user:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        return Response({"public_key": user.public_key}, status=status.HTTP_200_OK)
    
    except CustomUser.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(["GET"])
@permission_classes([AllowAny])
def get_group_members(requests):
    try:
        group_username = requests.query_params.get("group_username")
        user = requests.query_params.get("user")
        if not user:
            return Response({"error": "User is required"}, status=status.HTTP_400_BAD_REQUEST)

        if not group_username:
            return Response({"error": "Group username is required"}, status=status.HTTP_400_BAD_REQUEST)

        group = Group.objects.get(username=group_username)

        if not group:
            return Response({"error": "Group not found"}, status=status.HTTP_404_NOT_FOUND)

        members = group.members.all()

        if user not in members:
            return Response({"error": "User is not a member of the group"}, status=status.HTTP_403_FORBIDDEN)

        member_list = [member.username for member in members]

        return Response({"members": member_list}, status=status.HTTP_200_OK)
    
    except Group.DoesNotExist:
        return Response({"error": "Group not found"}, status=status.HTTP_404_NOT_FOUND)
    
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
