import PIL
from click import File
from fastapi import FastAPI, Request, HTTPException, status, Depends
from starlette.requests import Request
from starlette.responses import HTMLResponse
from tortoise import models
from tortoise.contrib.fastapi import register_tortoise
from models import *
from typing import Type
from pydantic import BaseModel
from token import tok_name
from auth import get_hashed_password

#Authentication
from auth import *
from fastapi.security import(OAuth2PasswordBearer, OAuth2PasswordRequestForm)
from typing import Union

#signals
from tortoise.signals import post_save
from typing import List, Optional, Type
from tortoise import BaseDBAsyncClient

#from emails import *

# response class
from fastapi.responses import HTMLResponse

#templates
from fastapi.templating import Jinja2Templates

# image upload

from fastapi import File ,UploadFile
import secrets 
from fastapi.staticfiles import StaticFiles
from PIL import Image
from PIL.Image import Image



app = FastAPI()

oath2_scheme = OAuth2PasswordBearer(tokenUrl='token')

# static file setup config

app.mount("/static", StaticFiles(directory="static"), name="static")



@app.post('/token')
async def generate_token(request_form : OAuth2PasswordRequestForm = Depends()):
    token = await token_generator(request_form.username, request_form.password)
    return {"access_token" : token, "token_type": "bearer"}

async def get_current_user(token: str = Depends(oath2_scheme)):
    try:
        payload = jwt.decode(token, config_credential['SECRET'], algorithms=['HS256'])
        user = await User.get(id = payload.get("id"))
    except:
        raise HTTPException(
            statue_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers= {"WWW-Authenticate": "Bearer"}
        )
    return await user


@app.post("/user/me")
async def user_login(user: Union[str , int] = Depends(get_current_user)):
    business = await Business.get(owner = user)
    logo = business.logo
    logo_path = "localhost:8000/static/images/"+logo

    return{
        "status": "ok",
        "data": {
            "username": user.username,
            "email" : user.email,
            "verified": user.is_verified,
            "joined_date": user.joined_date.strftime("%b %d %y"),
            "logo": logo_path
        }
    }


@post_save(User)
async def create_business(
    sender: "Type[User]",
    instance: User,
    created: bool,
    using_db: "Optional[BaseDBAsyncClient]",
    update_fields: List[str]
) -> None:
    if created:
        business_obj = await Business.create(
            business_name = instance.username, owner = instance
        )

        await business_pydantic.from_tortoise_orm(business_obj)
        #send the email
        await email_verification([instance.email], instance)



# @app.post("/register", include_in_schema=True)
# async def register_user(user: User Registration):
    # This endpoint should not require a token

@app.post("/registration")
async def user_registrations(user: user_pydanticIn): # type: ignore
    user_info = user.dict(exclude_unset=True) 
    user_info["password"] = get_hashed_password(user_info["password"])
    user_obj = await User.create(**user_info)
    new_user = await user_pydantic.from_tortoise_orm(user_obj)
    return{
        "status" : "ok",
        "data" : f"Hello {new_user.username}, thanks for choosing our services, please check your email inbox and click on the link to confirm your registration."
    }

templates = Jinja2Templates(directory="templates")

@app.get("/email_verification", response_class=HTMLResponse)
async def email_verification(request: Request, token: str):
    user = await very_token(token)

    if user and not user.is_verified:
        await user.save()
        return templates.TemplateResponse(
            "verification.html", {"request":request, "username" : user.username}
        )

    raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )

# @app.get("/")
# def index():
#     return {"Message": "Hello World"}


@app.post("/uploadfile/profile")
async def create_upload_file(file: UploadFile = File(...),
                                
                                
                                user:PIL.Image.Image = Depends(get_current_user)):
    FILEPATH = "./static/images"
    filename = file.filename
    
    extension = filename.split(".")[1]

    if extension not in ["png", "jpg"]:
        return{"status": "error", "detail": "File extension not allowed"}
    
    # u3u345kg.png
    taken_name = secrets.token_hex(10)+"."+extension
    generated_name = FILEPATH + tok_name 
    file_content = await file.read()

    with open(generated_name, "wb") as file:
        file.write(file_content)


#pillow

    img = Image.open(generated_name)
    img = img.resize(size= (200, 200))
    img.save(generated_name)

    file.close()

    business = await Business.get(owner = User)
    owner = await business.owner

    if owner == User:
        business.logo = tok_name 
        await business.save()
    
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="NOT AUTHENTICATED TO PERFORM THIS ACTION ",
            headers={"WWW-Authenticate": "Bearer"}
        )

    file_url = "localhost:8000" + generated_name[1:]
    return {"ststus" : "ok" , "filename" : file_url}

@app.post("/uploadfile/product/{id}")
async def create_upload_file(id: int, file: UploadFile = File(...),
                                user: PIL.Image.Image  = Depends(get_current_user)):


    FILEPATH = "./static/images"
    filename = file.filename
    
    extension = filename.split(".")[1]

    if extension not in ["png", "jpg"]:
        return{"status": "error", "detail": "File extension not allowed"}
    
    # u3u345kg.png
    taken_name = secrets.token_hex(10)+"."+extension
    generated_name = FILEPATH + tok_name 
    file_content = await file.read()

    with open(generated_name, "wb") as file:
        file.write(file_content)


#pillow

    img = Image.open(generated_name)
    img = img.resize(size= (200, 200))
    img.save(generated_name)

    file.close()
 
    product = await product.get(id = id)
    business = await product.business
    owner = await business.owner
 
    if owner == user:
        product.product_image = tok_name 
        await product.save()

    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="NOT AUTHENTICATED TO PERFORM THIS ACTION ",
            headers={"WWW-Authenticate": "Bearer"}
        )

    file_url = "localhost:8000" + generated_name[1:]
    return {"ststus" : "ok" , "filename" : file_url}


            
#  crud functionality

@app.post("/products")
async def add_new_product(product_pydanticIn,
                            user:Union[str , int] = Depends(get_current_user)):
    product = product.dict(exclude_unset=True)

    #to avoid division error by 0

    if product["original_price"] >0:
        product["pecentage_discount"] = ((product["original_price"] - product["new_price"]))/ product["original_price"] * 100


        product_obj = await product.create(**product,business = user)
        product_obj = await product_pydantic.from_tortoise_orm(product_obj)

        return{"status" : "ok" , "data":"product_obj"}

    else:
        return {"status": "error"}
    


@app.get("/product")
async def get_product():
    response = await product_pydantic.from_queryset(Product.all())
    return{"status" : "ok", "data" : response}


@app.get("/product/{id}")
async def get_product():
    product = await product.get(id =id)
    business = await product.business
    owner = await business.owner
    response = await product_pydantic.from_queryset_single(product.get(id =id))
    return {
        "status" : "ok",
        "data" :   { 
            "product_details" : response,
            "business_details" : {
                "name" : business.business_name,
                "city" :business.city,
                "region" : business.region,
                "description": business.business.description,
                "logo" :business.logo,
                "owner_id" : owner.id,
                "email" : owner.email,
                "join_date" : owner.join_date.striftime("%b %d %y")

            }
        }
    }



@app.delete("/products/{id}")
async def delete_product( id:int, user_pydantic = Depends(get_current_user)):
    product = await product.get(id =id)
    business = await product.business.business
    owner = await business.owner

    if User == owner:
        product.delete()

    else:
         raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="NOT AUTHENTICATED TO PERFORM THIS ACTION ",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return {"status" : "ok"}

@app.put("/product/{id}")
async def update_product(id : int,
                         update_info: int, str ,float, bolean ,char, Datetimefield,
                         user: str = Depends(get_current_user)):
    product = await product.get (id = id)
    business = await product.business
    owner = await business.owner

    update_info = update_info.dict(exclude_unset=True)
    update_info["date_published"]= datetime.utcnow()


    if user == owner and update_info["original_price"] > 0:
        update_info["percentage_discount"] = {(update_info["original_price"] ,
        update_info["new_price"]) / update_info[float]} * 100
        
        product = await product.update_from_dict(update_info)
        await product.save()
        response = await product_pydantic.from_tortoise_orm(product)
        return{"status" : "ok", "data": response}
    
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="NOT AUTHENTICATED TO PERFORM THIS ACTION  INVALID USER INPUT",
            headers={"WWW-Authenticate": "Bearer"}
        )

    

@app.put("/business/{id}")
async def update_business(id :int,
                          update_info: business_pydanticIn,   # type: ignore
                          user_pydantic = Depends(get_current_user)):
    update_business = update_business.dict()

    business = business.get(id = id)
    business_owner = await business_owner

    if User == business_owner:
        await business_owner.update_from_dict(update_business)
        business.save()
        response = await business_pydantic.from_tortoise_orm(business)
        return {"status" : "ok" , "data" : response}
        
    else:
         raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="NOT AUTHENTICATED TO PERFORM THIS ACTION  INVALID USER INPUT",
            headers={"WWW-Authenticate": "Bearer"}
        )




register_tortoise(
    app,  
    db_url = "sqlite://database.sqlite3",
    modules={"models" : ["models"]},
    generate_schemas= True,
    add_exception_handlers = True
)
