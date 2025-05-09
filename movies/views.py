from django.shortcuts import get_object_or_404
from rest_framework import generics,status
from . models import Movie, Cinema, Booking, Transaction
from .serializer import CinemaSerializer, MovieSerializer, BookingSerializer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated,IsAdminUser
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from django.db import transaction
import os, re, base64 , requests
from datetime import datetime
from dotenv import load_dotenv
from rest_framework.decorators import api_view, permission_classes
from django.http import JsonResponse, HttpResponseBadRequest
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.csrf import csrf_exempt

class SeatAvailabilityView(APIView):
    #RETURNS seats availabity for cinema
    def get(self,request,cinema_id):
        cinema=get_object_or_404(Cinema,id=cinema_id)
        return Response({"seating_chart": cinema.seating_chart}, status=status.HTTP_200_OK)

    
#List and create Movies
class MovieListCreateView(generics.ListCreateAPIView):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer

#Retrieve, update and delete Movies
class MovieDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer

#List and create Cinemas
class CinemaListCreateView(generics.ListCreateAPIView):
    serializer_class=CinemaSerializer
    def get_queryset(self):
        queryset=Cinema.objects.all()
        movie_id=self.request.query_params.get('movie_id')

        if movie_id:
            queryset=queryset.filter(movies__id=movie_id)
        return queryset

#list and create bookings
from django.db import transaction

class BookingListCreateView(APIView):
    permission_classes = [IsAuthenticated]  

    def get(self, request):
        bookings = Booking.objects.filter(user=request.user)
        serializer = BookingSerializer(bookings, many=True)
        return Response(serializer.data)

    @transaction.atomic  
    def post(self, request):
        user = request.user
        
        movie_id = request.data.get("movie_id")
        cinema_id = request.data.get("cinema_id")
        selected_seats = request.data.get("seats", [])
        booking_status = 'pending'  # ✅ Renamed to avoid conflict

        if not selected_seats:
            return Response({"message": "No seats selected"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            movie = get_object_or_404(Movie, id=movie_id)
            cinema = get_object_or_404(Cinema, id=cinema_id)

            with transaction.atomic():
                cinema.refresh_from_db()
                seating_chart = cinema.seating_chart  

                # Validate seat availability
                for row, col in selected_seats:
                    if seating_chart[row][col] == "X":  # "X" means booked
                        return Response({"message": f"Seat ({row}, {col}) is already booked"}, status=status.HTTP_400_BAD_REQUEST)

                # Mark seats as booked
                for row, col in selected_seats:
                    seating_chart[row][col] = "X"

                cinema.seating_chart = seating_chart
                cinema.save()

                # Save booking
                booking = Booking.objects.create(
                    user=user,
                    movie=movie,
                    cinema=cinema,
                    seats=selected_seats,
                    status=booking_status  # If your model has a status field
                )

                return Response({
                    "message": "Booking successful",
                    "booked_seats": selected_seats,
                    "booking_id": booking.id  # ✅ Include this!
                    }, status=status.HTTP_201_CREATED)


        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# Load environment variables
load_dotenv()

#RETRIVE ENVIRONMENT VARIABLES
CONSUMER_KEY = os.getenv('CONSUMER_KEY')
CONSUMER_SECRET = os.getenv('CONSUMER_SECRET')
MPESA_PASSKEY = os.getenv('MPESA_PASSKEY')

MPESA_SHORTCODE = os.getenv('MPESA_SHORTCODE')
CALLBACK_URL = os.getenv('CALLBACK_URL')
MPESA_BASE_URL = os.getenv('MPESA_BASE_URL')

# Generate M-Pesa access token
import base64

import json

def generate_access_token():
    try:
        print("[INFO] Generating access token...")

        credentials = f"{CONSUMER_KEY}:{CONSUMER_SECRET}"
        print(f"[DEBUG] Credentials: {credentials}")
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        print(f"[DEBUG] Encoded Credentials: {encoded_credentials}")

        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/json",
        }

        auth_url = f"{MPESA_BASE_URL}/oauth/v1/generate?grant_type=client_credentials"
        print(f"[DEBUG] Auth URL: {auth_url}")
        print(f"[DEBUG] Headers: {headers}")

        response = requests.get(auth_url, headers=headers)

        print(f"[DEBUG] Response Status Code: {response.status_code}")
        print(f"[DEBUG] Response Text: {response.text}")

        if response.status_code != 200:
            raise Exception(f"Failed to get access token: {response.text}")

        response_json = response.json()
        
        if "access_token" not in response_json:
            raise Exception(f"Access token missing in response: {response_json}")

        print("[INFO] Access token generated successfully.")
        return response_json["access_token"]

    except requests.RequestException as e:
        print(f"[ERROR] Failed to connect to M-Pesa: {str(e)}")
        raise Exception(f"Failed to connect to M-Pesa: {str(e)}")
    except json.JSONDecodeError:
        print("[ERROR] Failed to parse JSON response from M-Pesa.")
        raise Exception("Failed to parse JSON response from M-Pesa.")
    except Exception as e:
        print(f"[ERROR] Access token generation failed: {str(e)}")
        raise Exception(f"Access token generation failed: {str(e)}")



# Initiate STK Push and handle response
def initiate_stk_push(phone, amount):
    try:
        print("[INFO] Initiating STK Push...")

        token = generate_access_token()
        if not token:
            raise Exception("Failed to generate access token")

        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        stk_password = base64.b64encode(
            (MPESA_SHORTCODE + MPESA_PASSKEY + timestamp).encode()
        ).decode()

        request_body = {
            "BusinessShortCode": MPESA_SHORTCODE,
            "Password": stk_password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": phone,
            "PartyB": MPESA_SHORTCODE,
            "PhoneNumber": phone,
            "CallBackURL": CALLBACK_URL,
            "AccountReference": "account",
            "TransactionDesc": "Payment for goods",
        }

        print(f"[DEBUG] STK Push Payload: {json.dumps(request_body, indent=4)}")
        print(f"[DEBUG] Headers: {headers}")

        response = requests.post(
            f"{MPESA_BASE_URL}/mpesa/stkpush/v1/processrequest",
            json=request_body,
            headers=headers,
        )

        print(f"[DEBUG] STK Push Response Status: {response.status_code}")
        print(f"[DEBUG] STK Push Response Text: {response.text}")

        response.raise_for_status()

        response_json = response.json()

        if "ResponseCode" not in response_json:
            raise Exception(f"Unexpected M-Pesa response: {response_json}")

        print(f"[INFO] STK Push Request Successful: {response_json}")

        return response_json

    except requests.RequestException as e:
        print(f"[ERROR] Failed to connect to M-Pesa: {str(e)}")
        raise Exception(f"Failed to connect to M-Pesa: {str(e)}")
    except json.JSONDecodeError:
        print("[ERROR] Failed to parse JSON response from M-Pesa.")
        raise Exception("Failed to parse JSON response from M-Pesa.")
    except Exception as e:
        print(f"[ERROR] STK Push initiation error: {str(e)}")
        raise Exception(f"STK Push initiation error: {str(e)}")
    
# Phone number formatting and validation
def format_phone_number(phone):
    phone = phone.replace("+", "")
    if re.match(r"^254\d{9}$", phone):
        return phone
    elif phone.startswith("0") and len(phone) == 10:
        return "254" + phone[1:]
    else:
        raise ValueError("Invalid phone number format")

# API view to initiate payment
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initiate_payment(request):
    try:
        phone = request.data.get('phone_number')
        booking_id = request.data.get('booking_id')
        amount = request.data.get('amount')

        if not phone or not amount or not booking_id:
            return Response({"message": "Phone number, amount, and booking ID are required."}, status=status.HTTP_400_BAD_REQUEST)

        # Get booking and make sure it belongs to the user
        booking = get_object_or_404(Booking, id=booking_id, user=request.user)

        phone = format_phone_number(phone)
        amount = int(amount)

        # Call STK Push
        response = initiate_stk_push(phone, amount)

        if response.get("ResponseCode") == "0":
            checkout_id = response["CheckoutRequestID"]

            # ✅ Update booking status to paid
            booking.status = "paid"
            booking.save()

            # ✅ Save transaction
            Transaction.objects.create(
                user=request.user,
                booking=booking,
                phone_number=phone,
                amount=amount,
                checkout_request_id=checkout_id,
                status="pending"
            )

            return Response({
                "message": "Payment initiated successfully",
                "checkout_request_id": checkout_id,
                "booking_id": booking_id
            }, status=status.HTTP_200_OK)

        return Response({"message": "STK push failed"}, status=status.HTTP_400_BAD_REQUEST)

    except ValueError as ve:
        return Response({"message": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"message": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
# Query STK Push status
def query_stk_push(checkout_request_id):
    try:
        token = generate_access_token()
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password = base64.b64encode(
            (MPESA_SHORTCODE + MPESA_PASSKEY + timestamp).encode()
        ).decode()

        request_body = {
            "BusinessShortCode": MPESA_SHORTCODE,
            "Password": password,
            "Timestamp": timestamp,
            "CheckoutRequestID": checkout_request_id
        }

        response = requests.post(
            f"{MPESA_BASE_URL}/mpesa/stkpushquery/v1/query",
            json=request_body,
            headers=headers,
        )

        return response.json()

    except requests.RequestException as e:
        return {"error": str(e)}



@api_view(['POST'])
def stk_status_view(request):
    try:
        print("\n\n=== [DEBUG] stk_status_view HIT ===")
        print("[DEBUG] Incoming Data:", request.data)

        checkout_id = request.data.get("checkout_request_id")
        print("[DEBUG] Extracted checkout_request_id:", checkout_id)

        if not checkout_id:
            print("[ERROR] checkout_request_id is missing.")
            return Response({"message": "❌ Checkout Request ID is required"}, status=400)

        # Fetch the transaction from the database
        try:
            transaction = get_object_or_404(Transaction, checkout_request_id=checkout_id)
            print(f"[DEBUG] Transaction Found: ID={transaction.id}, Status={transaction.status}")
        except Exception as fetch_error:
            print("[ERROR] Failed to fetch transaction:", str(fetch_error))
            return Response({"message": "❌ Transaction not found"}, status=404)

        # 🟢 If transaction status is already success
        if transaction.status == "success":
            print("[DEBUG] Transaction already marked as SUCCESS.")
            return Response({
                "message": "✅ Payment already confirmed",
                "status": "success",
                "mpesa_receipt_number": transaction.mpesa_receipt_number or "N/A"
            })

        # 🔴 If transaction is failed
        elif transaction.status == "failed":
            print("[DEBUG] Transaction marked as FAILED.")
            return Response({
                "message": "❌ Payment failed",
                "status": "failed"
            })

        # ⏳ If status is still pending, query the M-Pesa API
        print("[DEBUG] Transaction still pending, querying M-Pesa API...")
        
        # Query the STK Push status from M-Pesa API
        status = query_stk_push(checkout_id)

        # Check if the query response contains the correct status
        if status.get("error"):
            print("[ERROR] Error querying STK status:", status["error"])
            return Response({"message": "❌ Error querying STK status"}, status=500)
        
        # Process the returned status from M-Pesa
        result_code = status.get("Body", {}).get("stkCallback", {}).get("ResultCode")
        result_desc = status.get("Body", {}).get("stkCallback", {}).get("ResultDesc")

        if result_code == 0:  # Payment was successful
            receipt = next((item["Value"] for item in status["Body"]["stkCallback"]["CallbackMetadata"]["Item"] if item["Name"] == "MpesaReceiptNumber"), None)
            transaction.status = "success"
            transaction.mpesa_receipt_number = receipt
            transaction.save()
            print(f"[DEBUG] Payment confirmed, receipt: {receipt}")
            return Response({
                "message": "✅ Payment confirmed",
                "status": "success",
                "mpesa_receipt_number": receipt
            })

        else:  # Payment failed
            transaction.status = "failed"
            transaction.save()
            print("[DEBUG] Payment failed.")
            return Response({
                "message": f"❌ Payment failed: {result_desc}",
                "status": "failed"
            })

    except Exception as e:
        print("[FATAL ERROR] stk_status_view Exception:", str(e))
        return Response({"message": f"❌ Internal server error: {str(e)}"}, status=500)

@api_view(['POST'])
def release_seats(request):
    booking_id = request.data.get('booking_id')
    if not booking_id:
        return Response({'error': 'Booking ID missing'}, status=400)


    booking = Booking.objects.filter(id=booking_id, paid=False).first()
    if booking:
        booking.delete()  # Or free the seats instead
        return Response({'message': 'Seats released'})
    return Response({'error': 'Booking not found or already paid'}, status=404)
@api_view(['POST'])
def update_payment_status(request):
    try:
        print("\n🔔 === [update_payment_status] Endpoint Hit ===")
        print("📩 Incoming Request Data:", request.data)

        data = request.data
        checkout_id = data.get("checkout_request_id")
        receipt = data.get("receipt_number")
        phone = data.get("phone")
        amount = data.get("amount")

        print(f"🔍 Extracted: Checkout ID: {checkout_id}, Receipt: {receipt}, Phone: {phone}, Amount: {amount}")

        if not all([checkout_id, receipt, phone, amount]):
            return Response({"message": "Missing required fields"}, status=400)

        try:
            transaction = Transaction.objects.get(checkout_request_id=checkout_id)
            print("✅ Transaction Found:", transaction.id)
        except Transaction.DoesNotExist:
            print("❌ Transaction not found for checkout_id:", checkout_id)
            return Response({"message": "Transaction not found"}, status=404)

        # 🟢 Check if transaction is already updated to success
        if transaction.status == "success":
            return Response({
                "message": "Payment already confirmed",
                "status": "success",
                "mpesa_receipt_number": transaction.mpesa_receipt_number
            })

        # Update transaction info
        transaction.status = "success"
        transaction.mpesa_receipt_number = receipt
        transaction.phone_number = phone
        transaction.amount = amount
        transaction.save()
        print("✅ Transaction Updated Successfully.")

        # Update related booking if exists
        if hasattr(transaction, 'booking'):
            transaction.booking.status = "booked"
            transaction.booking.save()
            print("✅ Related Booking Updated to 'booked'")
        else:
            print("ℹ️ No related booking found.")

        return Response({"message": "Payment confirmed via callback", "status": "success"})

    except Exception as e:
        print("🚨 Exception in update_payment_status:", str(e))
        return Response({"message": f"Error updating status: {str(e)}"}, status=500)

@csrf_exempt
@api_view(['POST'])
def mpesa_callback(request):
    print("🔔 Safaricom Callback Hit")
    print("📩 Raw Callback Data:", request.body)

    try:
        data = json.loads(request.body.decode('utf-8'))
        print("✅ JSON Parsed Data:", data)

        callback_data = data.get('Body', {}).get('stkCallback', {})
        print("📦 Callback Extracted:", callback_data)

        result_code = callback_data.get('ResultCode')
        checkout_id = callback_data.get('CheckoutRequestID')

        if result_code == 0:
            metadata = callback_data.get('CallbackMetadata', {}).get('Item', [])
            mpesa_data = {item['Name']: item.get('Value') for item in metadata}
            print("📊 Extracted M-Pesa Data:", mpesa_data)

            receipt = mpesa_data.get('MpesaReceiptNumber')
            amount = mpesa_data.get('Amount')
            phone = mpesa_data.get('PhoneNumber')
            transaction_date = mpesa_data.get('TransactionDate')

            # Check if transaction exists
            try:
                transaction = Transaction.objects.get(checkout_request_id=checkout_id)
                print("✅ Transaction Found:", transaction)

                # Update transaction
                transaction.status = "success"
                transaction.mpesa_receipt_number = receipt
                transaction.phone_number = phone
                transaction.amount = amount
                transaction.transaction_date = datetime.strptime(str(transaction_date), '%Y%m%d%H%M%S')
                transaction.save()
                print("✅ Transaction Updated")

                # Update booking if exists
                if transaction.booking:
                    transaction.booking.status = "booked"
                    transaction.booking.save()
                    print("✅ Booking Updated")

            except Transaction.DoesNotExist:
                print("❌ Transaction with checkout ID", checkout_id, "not found")

        else:
            print("❌ Payment was not successful. ResultCode:", result_code)

        return JsonResponse({"ResultCode": 0, "ResultDesc": "OK"})

    except Exception as e:
        print("💥 Callback Error:", str(e))
        return JsonResponse({"ResultCode": 1, "ResultDesc": f"Error: {str(e)}"})
# from django.views.decorators.csrf import csrf_exempt
# from django.http import JsonResponse, HttpResponseBadRequest
# @csrf_exempt  # To allow POST requests from external sources like M-Pesa
# def payment_callback(request):
#     if request.method != "POST":
#         return HttpResponseBadRequest("Only POST requests are allowed")

#     try:
#         callback_data = json.loads(request.body)  # Parse the request body
#         result_code = callback_data["Body"]["stkCallback"]["ResultCode"]

#         if result_code == 0:
#             # Successful transaction
#             checkout_id = callback_data["Body"]["stkCallback"]["CheckoutRequestID"]
#             metadata = callback_data["Body"]["stkCallback"]["CallbackMetadata"]["Item"]

#             amount = next(item["Value"] for item in metadata if item["Name"] == "Amount")
#             mpesa_code = next(item["Value"] for item in metadata if item["Name"] == "MpesaReceiptNumber")
#             phone = next(item["Value"] for item in metadata if item["Name"] == "PhoneNumber")

#             # Save transaction to the database
#             Transaction.objects.create(
#                 amount=amount, 
#                 checkout_id=checkout_id, 
#                 mpesa_code=mpesa_code, 
#                 phone_number=phone, 
#                 status="Success"
#             )
#             return JsonResponse({"ResultCode": 0, "ResultDesc": "Payment successful"})

#         # Payment failed
#         return JsonResponse({"ResultCode": result_code, "ResultDesc": "Payment failed"})

#     except (json.JSONDecodeError, KeyError) as e:
#         return HttpResponseBadRequest(f"Invalid request data: {str(e)}")




#kwa booking
"""try:
            movie=Movie.objects.get(id=movie_id)
            cinema=Cinema.objects.get(id=cinema_id)
            if cinema.capacity<seats:
                return Response({"message":"Not enough seats available"},status=status.HTTP_400_BAD_REQUEST)
            cinema.capacity-=seats
            cinema.save()
            booking=Booking(user=user,movie=movie,cinema=cinema,seats=seats)
            booking.save()
            return Response({"message":"Booking successful"},status=status.HTTP_201_CREATED)
        except Movie.DoesNotExist:
            return Response({"message":"Movie not found"},status=status.HTTP_404_NOT_FOUND)
        except Cinema.DoesNotExist:
            return Response({"message":"Cinema not found"},status=status.HTTP_404_NOT_FOUND)"
            """
