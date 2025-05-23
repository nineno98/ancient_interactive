from django.shortcuts import render, redirect, get_object_or_404
from .serializers import TerritorieSerializer, HistorieSerializer, CustomDrawSerializer, AncientPlacesSerializer,QuestionSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import Territorie, Historie, CustomDraw, Quiz, Question, Answer, UserAnswer, UserScore, AncientPlaces
from rest_framework.views import status
from .forms import LoginForm, QuizForm, QuestionTypeForm, QuestionForm, ValaszelemForm,IgazHamisForm
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
import geojson
from django.http import JsonResponse, HttpResponse, Http404
from rest_framework.permissions import IsAuthenticated
import json
import random
import sqlite3
import os
from django.conf import settings
from django.db.models import Count, Q, Sum, F
from django.db.models.functions import Coalesce
import logging
from django.contrib.auth.decorators import login_not_required

db_logger = logging.getLogger('db')


def sajatadatok(request):
    try:
        return render(request, 'users/user_informations.html')
    except Exception as e:
        messages.error(request, "Hiba történt a saját adatok oldal elérése során.")
        db_logger.error("Hiba: "+str(e))
        return redirect('fooldal')

def jelszovaltas(request):
    try:
        if request.method == 'POST':
            form = PasswordChangeForm(request.user, request.POST)
            if form.is_valid():
                
                form.save()
                update_session_auth_hash(request, form.user)
                db_logger.info(f"{request.user} sikeresen módosította a jelszavát.")
                messages.success(request, "A jelszó sikeresen módosítva! ")
                return redirect('sajatadatok')
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        db_logger.error(f"Hiba a {request.user} jelszóváltoztatása során: {error}")
                        messages.warning(request, f"{field}: {error}")
        else:
            form = PasswordChangeForm(request.user)
        return render(request, 'users/change_password.html', {'form':form})
    except Exception as e:
        db_logger.error("Hiba: "+str(e))
        messages.error(request, "Hiba történt a jelszó változtatás során!")
        return redirect('sajatadatok')

def terkep(request):
    try:
        return render(request, 'pages/map.html')
    except Exception as e:
        db_logger.error("Hiba a térkép oldal elérése során: "+str(e))
        messages.error(request, "Hiba történt a térkép oldal elérése során.")
        return redirect('fooldal')

def kijelentkezes(request):
    try:
        user = request.user
        logout(request)
        db_logger.info(f"{user} felhasználó kijelentkezett.")
        messages.success(request, "Kijelentkezve. Viszlát!")
        return redirect('fooldal')
    except Exception as e:
        db_logger.error("Hiba: "+str(e))
        messages.error(request, "Hiba történt a folyamat során.")
        return redirect('fooldal')

@login_not_required
def bejelentkezes(request):
    try:
        if request.method == 'POST':
            form = LoginForm(request.POST)
            if form.is_valid():
                username = form.cleaned_data['username']
                password = form.cleaned_data['password']
                user = authenticate(request, username=username, password=password)
                if user is not None:
                    login(request, user)
                    db_logger.info(f"{request.user} felhasználó bejelentkezett.")
                    messages.success(request, "Sikeres bejelentkezés")
                    return redirect('fooldal')
            
                else:
                    form = LoginForm()
                    messages.warning(request, "Sikertelen bejelentkezés. Hibás felhsználónév vagy jelszó")
                    return render(request, 'pages/login.html', {'form':form, 'message':'Sikertelen bejelentkezés. Hibás felhasználónév vagy jelszó!'})
            else:
                messages.error(request, "Hiba a belépés során! Ellenőrizze a felhasználónevet és jelszót!")
                return render(request, 'pages/login.html', {'form':form})
        form = LoginForm()
        return render(request, 'pages/login.html', {'form':form })
    except Exception as e:
        db_logger.error("Hiba: "+str(e))
        messages.error(request, "Hiba a bejelentkezés során.")
        return redirect('fooldal')
    
@login_not_required
def fooldal(request):
    try:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
            port = request.META.get('SERVER_PORT')
            qr = (ip+":"+port)
            qr_url = f"http://{ip}:{port}/"
        return render(request,'pages/home.html', {'qr':qr, 'qr_url':qr_url})
    except Exception as e:
        db_logger.error("Hiba a fooldal betöltése során: "+str(e))
        return HttpResponse("Hiba az oldal betöltése közben.")

# Rest framework

@api_view(['GET'])
def getTerritories(request):
    try:
        territories = Territorie.objects.all()
        serializer = TerritorieSerializer(territories, many = True)
        geojson_data = geojson.FeatureCollection(features=serializer.data)
        return JsonResponse(geojson_data)
    except Exception as e:
        db_logger.error("Hiba: "+str(e))
        response = {
            "status":"error",
            "message":"Hiba a kérés kiszolgálása során során."
        }
        return JsonResponse(response, status = 500)

@api_view(['GET'])
def getHistories(request):
    try:
        histories = Historie.objects.all()
        serializer = HistorieSerializer(histories, many = True, context={'request': request})
        geojson_data = geojson.FeatureCollection(features=serializer.data)
        return JsonResponse(geojson_data, safe=False)
    except Exception as e:
        db_logger.error("Hiba: "+str(e))
        response = {
            "status":"error",
            "message":"Hiba a kérés kiszolgálása során során."
        }
        return JsonResponse(response, status = 500)

def getAncientPlaces(request):
    try:
        ancient_places = AncientPlaces.objects.all()
        serializer = AncientPlacesSerializer(ancient_places, many=True)
        geojson_data = geojson.FeatureCollection(features=serializer.data)
        return JsonResponse(geojson_data, status = 200)
    except Exception as e:
        db_logger.error("Hiba: "+str(e))
        response = {
            "status":"error",
            "message":"Hiba a kérés kiszolgálása során során."
        }
        return JsonResponse(response, status = 500)

@method_decorator(csrf_exempt, name='dispatch')
class CustomDrawsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            customdraws = CustomDraw.objects.filter(created_by=request.user)
            serializer = CustomDrawSerializer(customdraws, many= True)
            geojson_data = geojson.FeatureCollection(features=serializer.data)
            return JsonResponse(geojson_data)
        except Exception as e:
            db_logger.error("Hiba: "+str(e))
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    def post(self, request): 
        try:
            
            serializer = CustomDrawSerializer(data=request.data, context={"request": request})
            if serializer.is_valid():
                #print("serializer valid")
                new_draw = serializer.save()
                
                response = {
                    "status":"success",
                    "object_id": new_draw.id
                }
                return JsonResponse(response, status = 200)
            else:
                response = {
                    "status":"error",
                    "message":serializer.errors
                }
                return JsonResponse(response, status = 400)
        except Exception as e:
            db_logger.error("Hiba: "+str(e))
            #print("error" +str(e))
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    def patch(self, request):
        try:
            obj_id = request.data.pop('id')
            if not obj_id:
                response = {
                    "status": "error",
                    "message": "ID megadása kötelező."
                }
                return JsonResponse(response, status=400)
            custom_draw = CustomDraw.objects.get(id = obj_id)
            if not custom_draw:
                response = {
                    "status":"error",
                    "message":"A módosítani kívánt elem nem található az adatbázisban."
                }
                return JsonResponse(response, status=404)
            serializer = CustomDrawSerializer(custom_draw, data=request.data, partial = True, context={"request": request})          
            if serializer.is_valid(raise_exception=True):
                #print(f"Validált adatok: {serializer.validated_data}")
                serializer.save()
                response = {
                    "status":"success",
                    "message":"Az elem módosítása sikeresen megtörtént."
                }
                return JsonResponse(response, status= 200)
        except Exception as e:
            db_logger.error("Hiba: "+str(e))
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    def delete(self, request):
        #remowend_id = request.data.get('id')
        #print(request.data.get('id'))
        try:
            remowend_id = request.data.get('id')
            obj = CustomDraw.objects.get(id=remowend_id)
            obj.delete()
            response = {
                "status":"success",
                "message":"Az elem törlése sikeresen megtörtént."
            }
            return JsonResponse(response, status=200)
        except CustomDraw.DoesNotExist as e:
            db_logger.error("Hiba: Az elem törlése sikertelen. Az elem nem található."+str(e))
            response = {
                "status":"error",
                "message":"Az elem törlése sikertelen. Az elem nem található."
            }
            return JsonResponse(response, status=404)
        except Exception as e:
            db_logger.error("Hiba: "+str(e))
            response = {
                "status":"error",
                "message":"Hiba a törlés során"
            }
            return JsonResponse(response, status=500)

def teszt(request):
    try:
        all_quizs = Quiz.objects.all()
        return render(request,'quiz/test.html',{"quiz_list":all_quizs})
    except Exception as e:
        db_logger.error("Hiba: "+str(e))
        messages.error(request, "Hiba a 'teszt' oldal betöltése során")
        return redirect('fooldal')

def uj_teszt_keszitese(request):
    try:
        if request.method == 'POST':
            
            form = QuizForm(request.POST)
            if form.is_valid():
                quiz = form.save(commit=False)
                quiz.created_by = request.user
                
                form.save()
                
                db_logger.info(f"A '{quiz.title}' teszt létrehozása sikeres.")
                messages.success(request, f"A '{quiz.title}' teszt létrehozása sikeres.")
                return redirect('teszt_reszletei', quiz_id=quiz.id)
            else:
                db_logger.error("Hiba történt, a teszt létrehozása sikertelen!")
                messages.error(request, "Hiba történt, a teszt létrehozása sikertelen!")
                return redirect('teszt_reszletei', quiz_id=quiz.id)
        else:
            form = QuizForm()
            return render(request, 'quiz/create_test.html', {"form":form})
    except Exception as e:
        db_logger.error("Hiba: "+str(e))
        messages.error(request, "Hiba a teszt létrehozása során.")
        return render(request, 'quiz/test.html', {"form": form})

def teszt_torlese(request, quiz_id):
    try:
        quiz = Quiz.objects.get(id = quiz_id)
        if not quiz:
            db_logger.error("Hiba: nincs teszt")
            messages.error(request, "Hiba történt a folyamat során!")
        quiz.delete()
        db_logger.info(f"A '{quiz.title}' teszt sikeresen törölve lett.")
        messages.success(request, f"A '{quiz.title}' teszt sikeresen törölve lett.")
        return redirect('teszt')
    except Exception as e:
        db_logger.error("Hiba: "+str(e))
        messages.error(request, "Hiba az teszt törlése során.")
        return redirect('teszt')


def teszt_reszletei(request, quiz_id):
    try:
        quiz = Quiz.objects.get(id = quiz_id)
        if not quiz:
            db_logger.error("Hiba: nincs teszt")
            messages.error(request, "Hiba történt a folyamat során!")
        if request.method == "POST":
            form = QuestionTypeForm(request.POST)
            if form.is_valid():
                question_type = form.cleaned_data["question_type"]
                return redirect("kerdes_hozzadasa", quiz_id=quiz.id, question_type=question_type)
            else:
                db_logger.error("Hiba: a form feldolgozása során")
                messages.error(request, "Hiba történt a folyamat során!")
        questions = quiz.questions.all()
        form = QuestionTypeForm()
        return render(request, "quiz/test_details.html", {
            "quiz": quiz,
            "questions": questions,
            "form": form
        })
    except Exception as e:
        db_logger.error("Hiba: "+str(e))
        #print(e)
        messages.error(request, "Hiba az oldal betöltése során.")
        return redirect('teszt')

def kerdes_hozzadasa(request, quiz_id, question_type):
    try:
        quiz = Quiz.objects.get(id = quiz_id)
        if not quiz:
            db_logger.error("Hiba: nincs teszt")
            messages.error(request, "Hiba történt a folyamat során!")
        if question_type == "mc":
            AnswerFormSetClass = ValaszelemForm
        else:
            AnswerFormSetClass = IgazHamisForm
        if request.method == "POST":
            answers_number = request.POST.get("answers-TOTAL_FORMS")
            for i in range(int(answers_number)):
                answer = request.POST.get(f"answers-{i}-text")
                if answer == "":
                    messages.warning(request, "Nem adott meg minden válaszelemhez választ!")
                    return redirect("teszt_reszletei", quiz_id=quiz.id)
            question_form = QuestionForm(request.POST)
            formset = AnswerFormSetClass(request.POST)
            if question_form.is_valid() and formset.is_valid():
                question = question_form.save(commit=False)
                question.quiz = quiz
                question.question_type = question_type
                question.save()
                answers = formset.save(commit=False)
                for answer in answers:
                    answer.question = question
                    answer.save()
                db_logger.info(f"Kérdés sikeresen létrehozva: {question}")
                messages.success(request, "A kérdés létrehozása sikeres")
                return redirect("teszt_reszletei", quiz_id=quiz.id)
        else:
            question_form = QuestionForm()
            formset = AnswerFormSetClass()
        return render(request, "quiz/create_question.html", {
            "quiz": quiz,
            "question_form": question_form,
            "formset": formset,
            "question_type": question_type
        })
    except Exception as e:
        db_logger.error("Hiba: "+str(e))
        messages.error(request, "Hiba a kérdés létrehozása során.")
        return redirect('teszt_reszletei', quiz_id=quiz_id)

def kerdes_kivalasztasa(request, quiz_id):
    try:
        quiz = Quiz.objects.get(id = quiz_id)
        if request.method == 'POST':
            selected_questions = request.POST.getlist('questions')
            
            if len(selected_questions) == 0:
                messages.warning(request, "Nem volt kiválasztva kérdés!")
                return redirect("teszt_reszletei", quiz_id=quiz.id)
            for question_id in selected_questions:                
                selected_question = Question.objects.get(id = question_id)
                selected_question.quiz = quiz
                selected_question.save()
            db_logger.info("A kérdések sikeresen hozzáadva!")
            messages.success(request, "A kérdések sikeresen hozzáadva!")
            return redirect("teszt_reszletei", quiz_id=quiz.id)
        questions = Question.objects.filter(~Q(quiz = quiz_id))
        return render(request, 'quiz/select_questions.html', {"questions":questions, "quiz":quiz})
    except Question.DoesNotExist as e:
        db_logger.error("Hiba: A kérdés nem található"+str(e))
        messages.error(request, "Hiba: A kérdés nem található!")
        return redirect("teszt_reszletei", quiz_id=quiz.id)
    except Quiz.DoesNotExist as e:
        db_logger.error("Hiba: a teszt nem található"+str(e))
        messages.error(request, "Hiba. A teszt nem található!")
        return redirect("teszt_reszletei", quiz_id=quiz.id)
    except Exception as e:
        db_logger.error("Hiba: "+str(e))
        messages.error(request, "Hiba a kérdések hozzáadása során!")
        return redirect("teszt_reszletei", quiz_id=quiz.id)

def kerdes_torlese(request, quiz_id, question_id):
    try:
        question = Question.objects.get(id = question_id)
        if not question:
            messages.error(request, "Hiba történt a folyamat során!")
            db_logger.error("Hiba: nincs kérdés")
        question.delete()
        db_logger.info(f"A '{question}' kérdés törlése sikeresen megtörtént.")
        messages.success(request,"Kérdés törlése sikeresen megtörtént.")
        return redirect('teszt_reszletei', quiz_id=quiz_id)
    except Exception as e:
        db_logger.error("Hiba: "+str(e))
        messages.error(request, "Hiba a kérdés törlése során.")
        return redirect('teszt_reszletei', quiz_id=quiz_id)

def teszt_inditasa(request, quiz_id):
    try:
        quiz = Quiz.objects.get(id = quiz_id)
        if not quiz:
            db_logger.error("Hiba. Az indítani kívánt teszt nem található.")
            messages.error(request, "Hiba. Az indítani kívánt teszt nem található.")
        if request.method == 'POST':
            score = 0
            user = request.user
            for question in quiz.questions.all():
                key = f"question_{question.id}"
                if key not in request.POST:
                    messages.error(request, f"Minden kérdésre válaszolnod kell! ({question.text})")
                    return redirect("teszt_inditasa", quiz_id=quiz_id)
                user_answer = request.POST[f'question_{question.id}']

                if question.question_type == "tf":
                    correct_answer = question.answers.first().is_correct
                    is_correct = (user_answer == "true" and correct_answer) or (user_answer == "false" and not correct_answer)

                    UserAnswer.objects.create(
                        user=user,
                        question=question,
                        selected_answer=question.answers.first(),
                        is_correct=is_correct,
                        points_awarded=question.points if is_correct else 0
                    )

                    if is_correct:
                        score += question.points

                else:
                    selected_answers = set(map(int, request.POST.getlist(f'question_{question.id}')))
                    correct_answers = set(question.answers.filter(is_correct=True).values_list('id', flat=True))
                    is_correct = selected_answers == correct_answers

                    for answer_id in selected_answers:
                        answer = Answer.objects.get(id=answer_id)
                        UserAnswer.objects.create(
                            user=user,
                            question=question,
                            selected_answer=answer,
                            is_correct=is_correct,
                            points_awarded=question.points if is_correct else 0
                        )

                    if is_correct:
                        score += question.points
            UserScore.objects.create(user=user, quiz=quiz, total_score=score)
            db_logger.info(f"A {quiz} teszt mentése sikeres.")
            messages.success(request, "A teszt mentése sikeres.")
            total_points = quiz.questions.aggregate(Sum('points'))['points__sum'] or 0
            return render(request, 'quiz/test_result.html', {'quiz': quiz, 'score': score, 'total_points':total_points})
        
        total_points = quiz.questions.aggregate(Sum('points'))['points__sum'] or 0
        questions = list(quiz.questions.all())
        random.shuffle(questions)
        return render(request, 'quiz/run_test.html', {'quiz': quiz, 'questions': questions})
    except Exception as e:
        db_logger.error("Hiba: "+str(e))
        messages.error(request, "Hiba teszt során")
        return redirect('teszt')

MBTILES_PATH = os.path.join(settings.BASE_DIR, "roman_map", "static", "tiles", "main_tile.mbtiles")
def serve_tile(request, z , x, y):
    try:
        
        if not os.path.exists(MBTILES_PATH):
            db_logger.error("Hiba: Adatbázis nem található")
            raise Http404("Adatbázis nem tálálható.")
            
        y_tms = (2 ** int(z)) - int(y) - 1
        conn = sqlite3.connect(MBTILES_PATH)
        cursor = conn.execute("SELECT tile_data FROM tiles WHERE zoom_level=? AND tile_column=? AND tile_row=?", (int(z), int(x), y_tms))
        result = cursor.fetchone()
        conn.close()
        if result:
            tile_data = result[0]
            return HttpResponse(tile_data, content_type = 'image/png')
        else:
            #raise Http404("Tile not found")
            return HttpResponse(status=404)
            
    except sqlite3.OperationalError as e:
        return HttpResponse(status=204)

    except sqlite3.IntegrityError as e:
        return HttpResponse(status=204)
    except sqlite3.DatabaseError as e:
        return HttpResponse(status=204)
    except Exception as e:
        return HttpResponse(status=204)


def teszteredmenyek(request, quiz_id):
    try:
        quiz = Quiz.objects.get(id = quiz_id)
        return render(request, 'quiz/test_chart.html', {"quiz_id": quiz.id})
        
    except Exception as e:
        db_logger.error("Hiba: "+str(e))
        #print(str(e))
        messages.error(request, "Hiba történt az oldal betöltése közben.")
        return redirect('teszt')

@api_view(['GET'])
def getTestQuestions(request, quiz_id):
    try:
        questions = Question.objects.filter(quiz = quiz_id).annotate(
            total_awarded_points = Coalesce(Sum('user_answers__points_awarded'),0),
            total_answers = Coalesce(Count('user_answers'),1),   
        )
        questions_data = []
        for question in questions:
            questions_data.append({
                "id": question.id,
                "text": question.text,
                "points":question.points,
                "total_awarded_points": question.total_awarded_points,
                "total_answers":question.total_answers           
            })
        return JsonResponse(questions_data, safe=False)
    except Question.DoesNotExist as e:
        db_logger.error("Hiba: "+str(e))
        messages.error(request, "Hiba az adatok lekérése közben.")
        response = {
            "status":"error",
            "message": "A kért Question objektum nem található"
        }
        return JsonResponse(response, safe=False, status=404)
    except Exception as e:
        db_logger.error("Hiba: "+str(e))
        messages.error(request, "Hiba az adatok lekérése közben.")
        response = {
            "status":"error",
            "message": "Hiba " + str(e)
        }
        return JsonResponse(response, safe=False, status=500)



