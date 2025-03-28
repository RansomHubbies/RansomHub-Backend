from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from users.models import CustomUser
from .messenger import pusher_client

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
    
