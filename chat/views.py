from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from users.models import CustomUser
from .messenger import pusher_client
from .models import Message, Group
import hashlib

@api_view(['POST'])
@permission_classes([AllowAny]) # Change to IsAuthenticated after testing
def send_message(request):
    """
    Send a message to a user
    """
    try:
        # Get the sender and recipient
        sender_username = request.data.get('sender')
        recipient_username = request.data.get('recipient')
        message = request.data.get('message')
        timestamp = request.data.get('timestamp')

        print(sender_username, recipient_username, message, timestamp
        )

        # verify that the sender and recipient exist
        sender = CustomUser.objects.get(username=sender_username)
        recipient = CustomUser.objects.get(username=recipient_username)

        if not sender or not recipient:
            return Response({"error": "Invalid sender or recipient"}, status=status.HTTP_400_BAD_REQUEST)

        print(f'Sender: {sender_username}, Recipient: {recipient_username}, Message: {message}, Timestamp: {timestamp}')
        
        # Send the message
        pusher_client.trigger(
            f'private-{recipient_username}',
            f'message',
            {
                'sender': sender_username,
                'message': message,
                'timestamp': timestamp
            },
        )
        return Response({"message": "Message sent"}, status=status.HTTP_200_OK)
    
    except CustomUser.DoesNotExist:
        return Response({"error": "Invalid sender or recipient"}, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        print(e)
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['POST'])
@permission_classes([AllowAny])
def create_group(request):
    """
    Create a group
    """
    try:
        # Get the group name and members
        group_name = request.data.get('name')
        members_usernames = request.data.get('members')

        # members is a list of usernames
        members = CustomUser.objects.filter(username__in=members_usernames)

        if not members:
            return Response({"error": "Invalid member"}, status=status.HTTP_400_BAD_REQUEST)
        
        base_string = group_name + "".join(members_usernames)
        username = hashlib.sha256(base_string.encode()).hexdigest()[:12]

        group = Group.objects.create(username=username, name=group_name)
        group.members.set(members)
        group.save()

        return Response({"message": "Group created"}, status=status.HTTP_201_CREATED)
    
    except CustomUser.DoesNotExist:
        return Response({"error": "Invalid member"}, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        print(e)
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
