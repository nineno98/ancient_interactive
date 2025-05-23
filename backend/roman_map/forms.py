from django import forms
from jsonschema import validate, ValidationError as JsonSchemaValidationError
import json
import os
from .models import Territorie, Historie, Quiz, CustomUser, Question, Answer, AncientPlaces
from .static.files import schema as ValidationsSchema
import pandas as pd
import re
from django.forms import inlineformset_factory, modelform_factory

class CustomUserXLSXImportForm(forms.Form):
    file = forms.FileField(label="XLSX fájl feltöltése")
    def clean_file(self):
        super().clean()
        try:
            file = self.cleaned_data.get('file')
            if not file.name.endswith(".xlsx"):
                raise forms.ValidationError("Csak .xlsx kiterjesztésű fájl engedélyezett.")
            df = pd.read_excel(file, engine='openpyxl')
            required_columns = {"first_name", "last_name", "status", "password"}
            if not required_columns.issubset(df.columns):
                raise forms.ValidationError(f"A fájl nem tartalmazza az összes szükséges mezőket: {required_columns}")
            for index, row in df.iterrows():
                historie_type = str(row['status'])
                if historie_type not in {'tanar', 'tanulo'}:
                    raise forms.ValidationError("Érvénytelen típusformátum. a típusnak 'csata' vagy 'esemeny' kell lennie.")
            self.cleaned_data["df"] = df
        
        except pd.errors.ParserError as e:
            raise forms.ValidationError(f"clean_file: A táblázat szerkezete hibás. {e}")
        except PermissionError as e:
            raise forms.ValidationError(f"clean_file: A fájlt nem lehet megnyitni. {e}")
        except ValueError as e:
            raise forms.ValidationError(f"clean_file: A fájl formátuma nem megfelelő. {e}")
        except FileNotFoundError as e:
            raise forms.ValidationError(f"clean_file: A fájl nem található: {e}")
        except Exception as e:
            raise forms.ValidationError(f"clean_file: Hiba: {e}")  
        return file
    def save(self):
        try:
            df = self.cleaned_data.get("df")
            for index, row in df.iterrows():
                status = row["status"]
                tanar = False
                tanulo = False
                if(status=="tanar"):
                    tanar = True
                    
                else:
                    tanulo = True
                
                user = CustomUser.objects.create(
                    
                    
                    tanulo = tanulo,
                    tanar = tanar,
                    first_name = row["first_name"],
                    last_name = row["last_name"]
                )
                user.set_password(row["password"])
                user.username = f"{status}{user.id}"
                user.save(update_fields=['password', 'username'])
        except Exception as e:
            print(e)


class AncientPlacesJSONForm(forms.Form):
    file = forms.FileField(required=True, label="Válasz egy geojson fájlt!")
    def clean_file(self):
        super().clean()
        try:
            file = self.cleaned_data.get('file')
            extension = os.path.splitext(file.name)[1].lower()
            if file:
                if extension != '.geojson':
                    raise forms.ValidationError('A feltöltött fájl kiterjesztése nem megfelelő!')
            else:
                raise forms.ValidationError('Nincs fájl feltöltve!')
            file_data = file.read().decode('utf-8')
            file.seek(0)
            json_data = json.loads(file_data)
            validate(instance=json_data, schema=ValidationsSchema)
        except OSError:
            raise forms.ValidationError('Hiba a fájl beolvasása közben!')
        except UnicodeDecodeError:
            raise forms.ValidationError('Hiba a fájl dekódolásánál. Nem érvényes utf-8 formátum!')
        except json.JSONDecodeError:
            raise forms.ValidationError('Hibás a JSON formátum!')
        except JsonSchemaValidationError as e:
            raise forms.ValidationError(f'Json validációs hiba: {e.message}')
        except Exception as e:
            raise e
        return file
    
    def save(self):
        try:
            uploaded_file = self.cleaned_data.get('file')
            file_data = uploaded_file.read().decode('utf-8')
            json_data = json.loads(file_data)
            feature_type = json_data.get('type')
            
            if feature_type == "FeatureCollection":
                if "features" in json_data:
                    features = json_data.get('features')
                    for feature in features:
                        modern_name = feature["properties"].get("modern_name", "A nem ismert")
                        AncientPlaces.objects.create(
                            modern_name=modern_name,
                            ancient_name=feature["properties"]["ancient_name"],
                            coordinates=feature["geometry"]["coordinates"]
                        )
                else:
                    raise forms.ValidationError("A 'features' kulcs hiányzik az objektumból.")
            elif feature_type == "Feature":
                modern_name = json_data["properties"].get("modern_name", "A nem ismert")
                AncientPlaces.objects.create(
                    modern_name = modern_name,
                    ancient_name = json_data["properties"]["ancient_name"],
                    coordinates = json_data["geometry"]["coordinates"]
                )
        except Exception as e:
            raise forms.ValidationError("Hiba a mentés során.")
        
class TerritoriesJSONForm(forms.Form):
    file = forms.FileField(required=True, label="Válasz egy geojson fájlt!")
    def clean_file(self):
        super().clean()   
        try:
            file = self.cleaned_data.get('file')
            extension = os.path.splitext(file.name)[1].lower()
            if file:
                if extension != '.geojson':
                    raise forms.ValidationError('A feltöltött fájl kiterjesztése nem megfelelő!')
            else:
                raise forms.ValidationError('Nincs fájl feltöltve!')
            file_data = file.read().decode('utf-8')
            file.seek(0)
            json_data = json.loads(file_data)
            validate(instance=json_data, schema=ValidationsSchema)
        except OSError:
            raise forms.ValidationError('Hiba a fájl beolvasása közben!')
        except UnicodeDecodeError:
            raise forms.ValidationError('Hiba a fájl dekódolásánál. Nem érvényes utf-8 formátum!')
        except json.JSONDecodeError:
            raise forms.ValidationError('Hibás a JSON formátum!')
        except JsonSchemaValidationError as e:
            raise forms.ValidationError(f'Json validációs hiba: {e.message}')
        except Exception as e:
            raise e
        
        return file
    
    def save(self):    
        try:
            uploaded_file = self.cleaned_data.get('file')
            file_data = uploaded_file.read().decode('utf-8')
            json_data = json.loads(file_data)
            feature_type = json_data.get('type')
            if feature_type == "FeatureCollection":
                if "features" in json_data:
                    features = json_data.get('features')
                    for item in features:
                        Territorie.objects.create(
                            name=item["properties"]["name"],
                            start_date=int(item["properties"]["start_date"]),
                            end_date=int(item["properties"]["end_date"]),
                            color=item["properties"]["color"],
                            coordinates=item["geometry"]["coordinates"]
                        )
                else:
                    raise forms.ValidationError("A 'features' kulcs hiányzik az objektumból.")
            elif feature_type == "Feature":
                Territorie.objects.create(
                    name=json_data["properties"]["name"],
                    start_date=int(json_data["properties"]["start_date"]),
                    end_date=int(json_data["properties"]["end_date"]),
                    color=json_data["properties"]["color"],
                    coordinates=json_data["geometry"]["coordinates"]
                )
            else:
                raise forms.ValidationError("Menteni kívánt fájl formátuma nem megfelelő.")
        except Exception as e:
            raise forms.ValidationError("Hiba lépett fel a fájl feldolgozása és mentése közben: "+str(e))

class LoginForm(forms.Form):
    username = forms.CharField(max_length = 30, label="Felhasználónév", required=True)
    password = forms.CharField(max_length = 30, label="Jelszó", widget= forms.PasswordInput, required=True)       

class HistorieXLSXImportForm(forms.Form):
    file = forms.FileField(label="XLSX fájl feltöltése")

    def clean_file(self):
        super().clean()
        try:
            file = self.cleaned_data.get('file')
            if not file.name.endswith(".xlsx"):
                raise forms.ValidationError("Csak .xlsx kiterjesztésű fájl engedélyezett.")
            df = pd.read_excel(file, engine='openpyxl')
            required_columns = {"name", "description", "coordinates", "time", "type"}
            if not required_columns.issubset(df.columns):
                raise forms.ValidationError(f"A fájl nem tartalmazza az összes szükséges mezőket: {required_columns}")
            for _, row in df.iterrows():
                coordinates = str(row["coordinates"]).strip()
                coordinate = coordinates.split(';')               
                if not (coordinates.startswith("[") and coordinates.endswith("]")):
                    raise forms.ValidationError(f"Érvénytelen koordináta formátum: {coordinates}")
                historie_type = str(row['type'])               
                if historie_type not in {'csata', 'esemeny'}:
                    raise forms.ValidationError("Érvénytelen típusformátum. a típusnak 'csata' vagy 'esemeny' kell lennie.")
            self.cleaned_data["df"] = df
            self.cleaned_data['coordinate'] = coordinate
        except pd.errors.ParserError as e:
            raise forms.ValidationError(f"clean_file: A táblázat szerkezete hibás. {e}")
        except PermissionError as e:
            raise forms.ValidationError(f"clean_file: A fájlt nem lehet megnyitni. {e}")
        except ValueError as e:
            raise forms.ValidationError(f"clean_file: A fájl formátuma nem megfelelő. {e}")
        except FileNotFoundError as e:
            raise forms.ValidationError(f"clean_file: A fájl nem található: {e}")
        except Exception as e:
            raise forms.ValidationError(f"clean_file: Hiba: {e}")  
        return file
    def save(self):
        try:
            df = self.cleaned_data.get("df")
            
            for _, row in df.iterrows():
                x = json.loads(str(row["coordinates"]))
                matches = re.findall(r"\[?([\d.]+),\s*([\d.]+)\]?", row["coordinates"]) 
                historie = Historie.objects.create(
                    name=row["name"],
                    description=row["description"],
                    coordinates = row["coordinates"],
                    historie_type = row["type"].lower(),
                    image = None,
                    date = row["time"]
                )
        except Exception as e:
            
            raise forms.ValidationError("Hiba a mentés során."+str(e))
            
                
class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ('title', 'description')

class ValaszelemForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ["text", "is_correct"]
        labels = {
            "text": "Válasz szövege",
            "is_correct": "Helyes válasz",
        }

class IgazHamisForm(forms.ModelForm):
    TRUE_FALSE_CHOICES = [
        (True, "Igaz"),
        (False, "Hamis"),
    ]

    is_correct = forms.ChoiceField(
        choices=TRUE_FALSE_CHOICES,
        widget=forms.RadioSelect,
        label="Igaz vagy hamis?",
        required=True
    )

    class Meta:
        model = Answer
        fields = ["is_correct"]
        labels = {
            "is_correct": "Igaz vagy hamis?",
        }

QuestionForm = modelform_factory(Question, fields=["text", "points"], labels={"text":"Kérdés", "points":"Elérhető pontszám"})
ValaszelemForm = inlineformset_factory(Question, Answer, form=ValaszelemForm, fields=["text", "is_correct"], extra=4)
IgazHamisForm = inlineformset_factory(Question, Answer,form=IgazHamisForm,fields=["is_correct"],extra=1,)
class QuestionTypeForm(forms.Form):
    question_type = forms.ChoiceField(
        choices=Question.QUESTION_TYPES,
        label="Válassz kérdés típust",
        widget=forms.Select(attrs={'class':'form-select form-select-sm',})
        
    )
        

AnswerFormSet = inlineformset_factory(
    Question,
    Answer,
    fields=['text', 'is_correct'],
    extra=4,
    can_delete=True
)
