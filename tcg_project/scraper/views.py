import logging
from django.http import JsonResponse
from .tasks import run_scraper
import os
import json
import base64
import hashlib
import requests
from OpenSSL import crypto
from rest_framework import status
from rest_framework.views import APIView
from dotenv import load_dotenv
import base64

load_dotenv()

auth_string = base64.b64encode(f'{os.getenv('CLIENT_ID')}:{os.getenv('CLIENT_SECRET')}'.encode('utf-8')).decode('utf-8')

logger = logging.getLogger(__name__)

def scrape_view(request):
    data = run_scraper()
    return JsonResponse(data, safe=False)


class EbayMarketplaceAccountDeletion(APIView):
    """
    Handles eBay Marketplace Account Deletion Webhook
    """
    # eBay Configuration
    CHALLENGE_CODE = 'challenge_code'
    VERIFICATION_TOKEN = os.getenv('VERIFICATION_TOKEN')
    ENDPOINT = os.getenv('ENDPOINT_URL')
    X_EBAY_SIGNATURE = 'X-Ebay-Signature'
    EBAY_BASE64_AUTHORIZATION_TOKEN = auth_string
    


    def __init__(self):
        super(EbayMarketplaceAccountDeletion, self).__init__()

    def get(self, request):
        """
        Get challenge code and return challengeResponse: challengeCode + verificationToken + endpoint
        :return: Response
        """
        challenge_code = request.GET.get(self.CHALLENGE_CODE)
        challenge_response = hashlib.sha256(challenge_code.encode('utf-8') +
                                            self.VERIFICATION_TOKEN.encode('utf-8') +
                                            self.ENDPOINT.encode('utf-8'))
        response_parameters = {
            "challengeResponse": challenge_response.hexdigest()
        }
        return JsonResponse(response_parameters, status=status.HTTP_200_OK)

    def post(self, request):
        """
        Return 200 status code and remove from db.
        See how to validate the notification here:
        https://developer.ebay.com/api-docs/commerce/notification/overview.html#use
        """
        # Verify notification is actually from eBay #
        # 1. Use a Base64 function to decode the X-EBAY-SIGNATURE header and retrieve the public key ID and signature
        x_ebay_signature = request.headers[self.X_EBAY_SIGNATURE]
        x_ebay_signature_decoded = json.loads(base64.b64decode(x_ebay_signature).decode('utf-8'))
        kid = x_ebay_signature_decoded['kid']
        signature = x_ebay_signature_decoded['signature']

        # 2. Call the getPublicKey Notification API method, passing in the public key ID ("kid") retrieved from the
        # decoded signature header. Documentation on getPublicKey:
        # https://developer.ebay.com/api-docs/commerce/notification/resources/public_key/methods/getPublicKey
        public_key = None
        try:
            ebay_verification_url = f'https://api.ebay.com/commerce/notification/v1/public_key/{kid}'
            oauth_access_token = self.get_oauth_token()
            headers = {
                'Authorization': f'Bearer {oauth_access_token}'
            }
            public_key_request = requests.get(url=ebay_verification_url, headers=headers, data={})
            if public_key_request.status_code == 200:
                public_key_response = public_key_request.json()
                public_key = public_key_response['key']
        except Exception as e:
            message_title = "Ebay Marketplace Account Deletion: Error calling getPublicKey Notfication API."
            logger.error(f"{message_title} Error: {e}")
            return JsonResponse({}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 3. Initialize the cryptographic library to perform the verification with the public key that is returned from
        # the getPublicKey method. If the signature verification fails, an HTTP status of 412 Precondition Failed is returned.
        pkey = crypto.load_publickey(crypto.FILETYPE_PEM, self.get_public_key_into_proper_format(public_key))
        certification = crypto.X509()
        certification.set_pubkey(pkey)
        notification_payload = request.body
        signature_decoded = base64.b64decode(signature)
        try:
            crypto.verify(certification, signature_decoded, notification_payload, 'sha1')
        except crypto.Error as e:
            message_title = f"Ebay Marketplace Account Deletion: Signature Invalid. " \
                            f"The signature is invalid or there is a problem verifying the signature. "
            logger.warning(f"{message_title} Error: {e}")
            return JsonResponse({}, status=status.HTTP_412_PRECONDITION_FAILED)
        except Exception as e:
            message_title = f"Ebay Marketplace Account Deletion: Error performing cryptographic validation."
            logger.error(f"{message_title} Error: {e}")
            return JsonResponse({}, status=status.HTTP_412_PRECONDITION_FAILED)

        # Take appropriate action to delete the user data. Deletion should be done in a manner such that even the
        # highest system privilege cannot reverse the deletion #
        # TODO: Replace with your own data removal here

        # Acknowledge notification reception
        return JsonResponse({}, status=status.HTTP_200_OK)

    def get_oauth_token(self):
        """
        Returns the OAuth Token from eBay which can be used for making other API requests such as getPublicKey
        """
        url = 'https://api.ebay.com/identity/v1/oauth2/token'
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': f"Basic {self.EBAY_BASE64_AUTHORIZATION_TOKEN}"
        }
        payload = 'grant_type=client_credentials&scope=https%3A%2F%2Fapi.ebay.com%2Foauth%2Fapi_scope'
        request = requests.post(url=url, headers=headers, data=payload)
        data = request.json()
        return data['access_token']

    @staticmethod
    def get_public_key_into_proper_format(public_key):
        """
        Public key needs to have \n in places to be properly assessed by crypto library.
        """
        return public_key[:26] + '\n' + public_key[26:-24] + '\n' + public_key[-24:]


