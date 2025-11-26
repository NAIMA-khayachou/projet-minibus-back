from fastapi import FastAPI

#  on crée notreapplication fastapi
app = FastAPI()

# qund qulqu'un va visiter la page d'accueil 
@app.get("/")
def root():
    return {"message": "API is running!"}
