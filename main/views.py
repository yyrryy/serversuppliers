
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from .models import Category, Client, Order, Orderitem, Produit, Client, Mark, Represent, Bonlivraison, Ordersnotif, Connectedusers, Promotion, Refstats, Cart, Cartitems, Notavailable, Wishlist, Wich, Notification
# import pandas as pd
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout
import json
from django.db.models import OuterRef, Exists, Count, Q, F, Sum, Case, When, Value, IntegerField
# import csrf_exampt
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.shortcuts import reverse
import datetime
from django.utils import timezone
from .models import UserSession
import telegram
import asyncio
import requests as req
TOKEN = '6716455240:AAFgHhoQLrmCU8Elc_A_DQFLrwCJtsHk3P8'
user_chat_ids = ['USER_CHAT_ID_1', 'USER_CHAT_ID_2', 'USER_CHAT_ID_3']
group_chat_id = '-4156'


def tocatalog(user):
    return (user.groups.filter(name='salsemen').exists() or user.groups.filter(name='clients').exists() or user.groups.filter(name='admin').exists() )



def product(request, id):
    product=Produit.objects.get(pk=id)
    simillars=Produit.objects.filter(Q(refeq1__icontains=product.ref)|Q(refeq2__icontains=product.ref)).exclude(pk=id)
    print('>>>>>>>>', simillars, product.ref)
    ctx={
        'product':product, 
        'title':product.name,
        'simillars':simillars,
        'diamteres':product.diametre.split('*') if product.diametre else ['-','-','-','-','-']
    }
    if product.cars:
        ctx['cars']=json.loads(product.cars)
    return render(request, 'product.html', ctx)

@csrf_exempt
def searchref(request):
    ref=request.POST.get('ref')
    products = Produit.objects.filter(Q(ref__icontains=ref) | Q(name__icontains=ref) | Q(cars__icontains=ref) | Q(coderef__icontains=ref) | Q(equivalent__icontains=ref) | Q(refeq1__icontains=ref) | Q(refeq2__icontains=ref) | Q(refeq3__icontains=ref) | Q(refeq4__icontains=ref) | Q(diametre__icontains=ref) | Q(coderef__icontains=ref))
    return render(request, 'searchpage.html', {'products':products, 'title':'Recherche'})

def searchrefphone(request):
    ref=request.GET.get('ref').strip()
    a=""
    if not '+' in ref:
        products=Produit.objects.filter(ref__istartswith=ref).order_by('-stocktotal')
        q_objects = Q()

        q_objects &= (Q(ref__icontains=ref) | Q(coderef__icontains=ref) | Q(name__icontains=ref) | Q(category__name__icontains=ref) |  Q(mark__name__icontains=ref) |  Q(equivalent__icontains=ref)  |  Q(refeq1__icontains=ref) |  Q(refeq2__icontains=ref)  |  Q(block__icontains=ref) | Q(refeq1__icontains=ref) | Q(refeq1__icontains=ref) | Q(sellprice__icontains=ref)  | Q(buyprice__icontains=ref)  | Q(cars__icontains=ref)  | Q(diametre__icontains=ref))
        products=products | Produit.objects.filter(q_objects).exclude(sellprice=0).order_by('-stocktotal')[:50]
        apiproducts=req.get(f'http://167.71.77.64/searcher/searchforibra?ref={ref}')
        oem=''
        if len(products)==0:
            try:
                oem=json.loads(req.get(f'http://167.71.77.64/searcher/searchforsupplier?ref={ref}').content.decode('utf-8'))['oem'].strip().lower()
            except Exception as e:
                oem=str(e)
            if oem!="":
                products=Produit.objects.filter(Q(ref=oem) | Q(equivalent__icontains=oem)).exclude(sellprice=0).order_by('-stocktotal')[:50]
        brands = [product.mark for product in products if product.mark]
        categories = [product.category for product in products if product.category]

        unique_categories = set(categories)
        unique_brands = set(brands)
        brands = [{'id': mark.id, 'name': mark.name, 'image':mark.image.url if mark.image else '/media/default.png'} for mark in unique_brands]
        categories = [{'id': category.id, 'name': category.name, 'image':category.image.url if category.image else '/media/default.png'} for category in unique_categories]
        for i in products:
            if i.stocktotal<=0:
                status="indisponible"
            elif i.stocktotal>=5:
                status="disponible"
            else:
                status="soon"
            if request.user.groups.first().name=='clients':
                a+=f"""
                    <div class="suggestions__item suggestions__product border mb-2 productsbrand{i.mark.id if i.mark else ''} productscategorycat{i.category.id if i.category else ''}">
                    <div class="suggestions__product-image image image--type--product">
                        <div class="image__body">
                        <a href='/product/{i.id}' terget='_blank'>
                            <img class="image__tag" src="{i.image.url if i.image else ""}" alt="">
                        </a>
                        </div>
                    
                    </div>
                    <div class="suggestions__product-info">
                        <div class="suggestions__product-name">
                        <strong class="text-blue">{i.ref.upper()}</strong>  <strong style="margin-left:75px;">Résultats de rercherche pour: {ref}</strong><br>
                        <strong style="color:red;">{i.refeq1.upper() if i.refeq1 else ''}</strong> <br>
                        <strong style="color:blue;">{i.refeq2.upper() if i.refeq2 else ''}</strong> <br>
                        <strong style="color:blue;">{i.diametre if i.diametre else ''}</strong> <br>
                        <strong style="color:red; font-size:20px;">{i.refeq3.upper() if i.refeq3 else ''}</strong>
                        </div>
                        <div class="suggestions__product-name"> {i.name} </div>
                        <div class="d-flex justify-content-between">
                            <div class="status {status}"></div>
                            

                            
                        </div>
                    
                    </div>
                        <div class="d-flex flex-column">

                        <div class="suggestions__product-price text-orange"> 
                            {i.sellprice} {i.remise if i.remise > 0 else ("NET")}% 
                        </div>
                        <div>
                        <img src="{i.mark.image.url if i.mark and i.mark.image else ''}" width=80>
                        </div>
                        <div class="d-flex flex-column mt-auto" style="width: 8vw;">

                            <div class="cart-table__quantity input-number">
                            <input style="height: 2.5em;" class="form-control input-number__input qty" type="number" min="1" value="1">
                            </div>
                            <button class="btn btn-success cmnd" pdct="{i.id}" pdctref="{i.ref}" pdctname="{i.name}" pdctpr="{i.sellprice}" pdctid="{i.id}" pdctimg="{ i.image.url if i.image else '' }" pdctremise="{i.remise}" pdctcategory="" onclick="{'whishlist(event)'if i.stocktotal <= 0 else 'cmnd(event)'}">{'Rliquat'if i.stocktotal <= 0 else 'Cmnd'}</button>
                            <button class="btn btn-info mt-2 d-none anullercmnd" data-id="{i.id}" onclick="anullercmnd(event, '{i.id}')"> Anuller </button>
                        </div>
                        </div>
                    </div>
                """
            else:
                a+=f"""
                    <div class="suggestions__item suggestions__product border mb-2 productsbrand{i.mark.id if i.mark else ''} productscategorycat{i.category.id if i.category else ''}">
                    <div class="suggestions__product-image image image--type--product">
                        <div class="image__body">
                        <a href='/product/{i.id}' terget='_blank'>
                            <img class="image__tag" src="{i.image.url if i.image else ""}" alt="">
                        </a>
                        </div>
                    
                    </div>
                    <div class="suggestions__product-info">
                        <div class="suggestions__product-name">
                        <strong class="text-blue">{i.ref.upper()}</strong> <br>
                        <strong style="color:red;">{i.refeq1.upper() if i.refeq1 else ''}</strong> <br>
                        <strong style="color:blue;">{i.refeq2.upper() if i.refeq2 else ''}</strong> <br>
                        <strong style="color:blue;">{i.diametre if i.refeq2 else ''}</strong> <br>
                        <strong style="color:red; font-size:20px;">{i.refeq3.upper() if i.refeq3 else ''}</strong>
                        </div>
                        <div class="suggestions__product-name"> {i.name} </div>
                        <div class="d-flex justify-content-between">
                            <div class="status {status}"></div>
                            
    
                        
                        </div>
                    
                    </div>
                        <div class="d-flex flex-column">

                        <div class="suggestions__product-price text-orange"> 
                            {i.sellprice} {i.remise if i.remise > 0 else ("NET")}% 
                        </div>
                        <div>
                        <img src="{i.mark.image.url if i.mark and i.mark.image else ''}" width=80>
                        </div>
                        <div class="d-flex flex-column mt-auto" style="width: 8vw;">

                            <div class="cart-table__quantity input-number">
                            <input style="height: 2.5em;" class="form-control input-number__input qty" type="number" min="1" value="1">
                            </div>
                            <button class="btn btn-primary cmnd" pdct="{i.id}" pdctref="{i.ref}" pdctname="{i.name}" pdctpr="{i.sellprice}" pdctid="{i.id}" pdctimg="{ i.image.url if i.image else '/media/default.png' }" pdctremise="{i.remise}" pdctcategory="" onclick="cmnd(event)">Cmnd</button>
                            <button class="btn btn-info mt-2 d-none anullercmnd" data-id="{i.id}" onclick="anullercmnd(event, '{i.id}')"> Anuller </button>
                        </div>
                        </div>
                    </div>
                """
        return JsonResponse({'data':a, 'brands':brands, 'categories':categories, 'apiproducts':apiproducts.content.decode('utf-8') if not '+' in ref else None, "oem":oem})
        
    else:
        search_terms = ref.split('+')
        # Create a list of Q objects for each search term and combine them with &
        q_objects = Q()
        for term in search_terms:
            if term:
                # term = ''.join(char for char in term if char.isalnum())
                q_objects &= (Q(ref__icontains=term) | Q(coderef__icontains=term) | Q(name__icontains=term) | Q(category__name__icontains=term) |  Q(mark__name__icontains=term) |  Q(equivalent__icontains=term)  |  Q(refeq1__icontains=term) |  Q(refeq2__icontains=term)  |  Q(block__icontains=term) | Q(refeq1__icontains=term) | Q(refeq1__icontains=term) | Q(sellprice__icontains=term)  | Q(buyprice__icontains=term)  | Q(cars__icontains=term)  | Q(diametre__icontains=term))
        products=Produit.objects.filter(q_objects).exclude(sellprice=0).order_by('-stocktotal')[:50]
        
        #products = Produit.objects.filter(Q(ref__icontains=ref) | Q(name__icontains=ref) | Q(cars__icontains=ref) | Q(coderef__icontains=ref) | Q(equivalent__icontains=ref) | Q(refeq1__icontains=ref) | Q(refeq2__icontains=ref) | Q(refeq3__icontains=ref) | Q(refeq4__icontains=ref) | Q(diametre__icontains=ref))
        brands = [product.mark for product in products if product.mark]
        categories = [product.category for product in products if product.category]

        unique_categories = set(categories)
        unique_brands = set(brands)
        brands = [{'id': mark.id, 'name': mark.name, 'image':mark.image.url if mark.image else '/media/default.png'} for mark in unique_brands]
        categories = [{'id': category.id, 'name': category.name, 'image':category.image.url if category.image else '/media/default.png'} for category in unique_categories]
        for i in products:
            if i.stocktotal<=0:
                status="indisponible"
            elif i.stocktotal>=5:
                status="disponible"
            else:
                status="soon"
            # <img src="{i.carlogos.image.url if i.carlogos and i.carlogos.image else ''}" width="40" style="width:40px;">
            if request.user.groups.first().name=='clients':
                a+=f"""
                    <div class="suggestions__item suggestions__product border mb-2 productsbrand{i.mark.id if i.mark else ''} productscategorycat{i.category.id if i.category else ''}">
                    <div class="suggestions__product-image image image--type--product">
                        <div class="image__body">
                        <a href='/product/{i.id}' terget='_blank'>
                            <img class="image__tag" src="{i.image.url if i.image else ""}" alt="">
                        </a>
                        </div>
                    
                    </div>
                    <div class="suggestions__product-info">
                        <div class="suggestions__product-name">
                        <strong class="text-blue">{i.ref.upper()}</strong>  <strong style="margin-left:75px;">Résultats de rercherche pour: {ref}</strong><br>
                        <strong style="color:red;">{i.refeq1.upper() if i.refeq1 else ''}</strong> <br>
                        <strong style="color:blue;">{i.refeq2.upper() if i.refeq2 else ''}</strong> <br>
                        <strong style="color:blue;">{i.diametre if i.diametre else ''}</strong> <br>
                        <strong style="color:red; font-size:20px;">{i.refeq3.upper() if i.refeq3 else ''}</strong>
                        </div>
                        <div class="suggestions__product-name"> {i.name} </div>
                        <div class="d-flex justify-content-between">
                            <div class="status {status}"></div>
                            
                            
                            
                        </div>
                    
                    </div>
                        <div class="d-flex flex-column">

                        <div class="suggestions__product-price text-orange"> 
                            {i.sellprice} {i.remise if i.remise > 0 else ("NET")}% 
                        </div>
                        <div>
                        <img src="{i.mark.image.url if i.mark and i.mark.image else ''}" width=80>
                        </div>
                        <div class="d-flex flex-column mt-auto" style="width: 8vw;">

                            <div class="cart-table__quantity input-number">
                            <input style="height: 2.5em;" class="form-control input-number__input qty" type="number" min="1" value="1">
                            </div>
                            <button class="btn btn-success cmnd" pdct="{i.id}" pdctref="{i.ref}" pdctname="{i.name}" pdctpr="{i.sellprice}" pdctid="{i.id}" pdctimg="{ i.image.url if i.image else '' }" pdctremise="{i.remise}" pdctcategory="" onclick="{'whishlist(event)'if i.stocktotal <= 0 else 'cmnd(event)'}">{'Rliquat'if i.stocktotal <= 0 else 'Cmnd'}</button>
                            <button class="btn btn-info mt-2 d-none anullercmnd" data-id="{i.id}" onclick="anullercmnd(event, '{i.id}')"> Anuller </button>
                        </div>
                        </div>
                    </div>
                """
            else:
                a+=f"""
                    <div class="suggestions__item suggestions__product border mb-2 productsbrand{i.mark.id if i.mark else ''} productscategorycat{i.category.id if i.category else ''}">
                    <div class="suggestions__product-image image image--type--product">
                        <div class="image__body">
                        <a href='/product/{i.id}' terget='_blank'>
                            <img class="image__tag" src="{i.image.url if i.image else ""}" alt="">
                        </a>
                        </div>
                    
                    </div>
                    <div class="suggestions__product-info">
                        <div class="suggestions__product-name">
                        <strong class="text-blue">{i.ref.upper()}</strong> <br>
                        <strong style="color:red;">{i.refeq1.upper() if i.refeq1 else ''}</strong> <br>
                        <strong style="color:blue;">{i.refeq2.upper() if i.refeq2 else ''}</strong> <br>
                        <strong style="color:blue;">{i.diametre if i.refeq2 else ''}</strong> <br>
                        <strong style="color:red; font-size:20px;">{i.refeq3.upper() if i.refeq3 else ''}</strong>
                        </div>
                        <div class="suggestions__product-name"> {i.name} </div>
                        <div class="d-flex justify-content-between">
                            <div class="status {status}"></div>
                            
    
                        
                        </div>
                    
                    </div>
                        <div class="d-flex flex-column">

                        <div class="suggestions__product-price text-orange"> 
                            {i.sellprice} {i.remise if i.remise > 0 else ("NET")}% 
                        </div>
                        <div>
                        <img src="{i.mark.image.url if i.mark and i.mark.image else ''}" width=80>
                        </div>
                        <div class="d-flex flex-column mt-auto" style="width: 8vw;">

                            <div class="cart-table__quantity input-number">
                            <input style="height: 2.5em;" class="form-control input-number__input qty" type="number" min="1" value="1">
                            </div>
                            <button class="btn btn-primary cmnd" pdct="{i.id}" pdctref="{i.ref}" pdctname="{i.name}" pdctpr="{i.sellprice}" pdctid="{i.id}" pdctimg="{ i.image.url if i.image else '/media/default.png' }" pdctremise="{i.remise}" pdctcategory="" onclick="cmnd(event)">Cmnd</button>
                            <button class="btn btn-info mt-2 d-none anullercmnd" data-id="{i.id}" onclick="anullercmnd(event, '{i.id}')"> Anuller </button>
                        </div>
                        </div>
                    </div>
                """
        return JsonResponse({'data':a, 'brands':brands, 'categories':categories, 'apiproducts':apiproducts.content.decode('utf-8') if not '+' in ref else None})

@user_passes_test(tocatalog, login_url='main:loginpage')
@login_required(login_url='main:loginpage')
def clientshome(request):
    request.session.set_expiry(90 * 24 * 60 * 60)
    marks = Mark.objects.annotate(
        has_promotion=Exists(Produit.objects.filter(mark_id=OuterRef('pk'), isoffer=True)),
        total_products=Count('produit')
    )
    categories = Category.objects.all().order_by('code').annotate(
        has_promotion=Exists(Produit.objects.filter(mark_id=OuterRef('pk'), isoffer=True)),
        total_products=Count('produit')
    )
    ctx={
        'categories': categories,
        'clients':Client.objects.all(),
        'marques':marks,
        'promotions':Promotion.objects.order_by('info').exclude(info__startswith='ARRIVAGE').exclude(info=''),
        'arrivage':Promotion.objects.filter(info__startswith='ARRIVAGE'),
        'newproducts':Produit.objects.filter(isnew=True).order_by('category')
    }
    return render(request, 'clientshome.html', ctx)

# users groups
# chack if user's group in accounting
def isaccounting(user):
    return (user.groups.filter(name='accounting').exists() or user.groups.filter(name='admin').exists() )

# chack if user's group in salsemen
def issalsemen(user):
    return user.groups.filter(name='salsemen').exists() and user.is_active

def isclient(user):
    return user.groups.filter(name='clients').exists() and user.is_active


def bothsalseaccount(user):
    return (user.groups.filter(name='salsemen').exists() or user.groups.filter(name='accounting').exists() or user.groups.filter(name='admin').exists() )

def isadmin(user):
    return user.groups.filter(name='admin').exists()


# Create your views here.
def home(request):
    ctx={
        'promotion':Promotion.objects.order_by('info'),
        'titel':'Accueil'
    }
    # print(request.user)
    # print(request.user.groups.first())
    # if request.user.groups.first():
    #     if (request.user.groups.first().name=='salsemen'):
    #         return redirect(catalog)
    #     if (request.user.groups.first().name=='accounting'):
    #         return redirect('main:orders')
    #     if (request.user.groups.first().name=='admin'):
    #         return redirect('main:orders')
    # return redirect('main:loginpage')
    return render(request, 'login.html', ctx)


def about(request):
    return render(request, 'about.html')
def partners(request):
    return render(request, 'marques.html')

def profile(request):
    return render(request, 'profile.html')

def loginpage(request):
    print('groups', request.user.groups.all())
    print('>>>>>>>>>>>',request.user)
    if request.user.groups.all():
        if (request.user.groups.first().name=='salsemen'):
            #usersession = UserSession.objects.filter(user=request.user).first()
            #print(usersession, 'user session')
            #if usersession:
                # If the user is already authenticated, log them out
                #print('user already get methode usersession')
                #return redirect('main:logoutuser')
            if request.user.is_active:
                request.session.set_expiry(30 * 24 * 60 * 60)
                # UserSession.objects.create(user=request.user)
                print('user is active')
                return redirect('main:catalogpage')
            else:
                return redirect ('main:loginpage')
        if (request.user.groups.first().name=='accounting'):
            return redirect('main:orders')
        # if (request.user.groups.first().name=='admin'):
        #     return redirect('main:ibra')
        if (request.user.groups.first().name=='clients'):
            # print('user logied in')
            # usersession = UserSession.objects.filter(user=request.user).first()
            # print(usersession, 'user session')
            # if usersession:
            #     # If the user is already authenticated, log them out
            #     print('user already get methode usersession')
            #     return redirect('main:logoutuser')
            if request.user.is_active:
                print('>>>>>>>>>extending')
                # make user always connected finish this
                request.session.set_expiry(30 * 24 * 60 * 60)
                print('user is active')
                return redirect('main:clientshome')
            else:
                return redirect ('main:loginpage')
    return render(request, 'login.html')

def loginuser(request):
    username = request.POST.get('username', '')
    password = request.POST.get('password', '')
    if username=='' or password=='':
        return redirect('main:loginpage')
    print(username, password)
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    user = authenticate(request, username=username, password=password)
    print('>>>>>>>><', user)
    if user is not None:
        
        if not len(user.groups.all()):
            return redirect('main:login')
        group=user.groups.all().first().name
        print('goutp', group)
        if group == 'salsemen':
            # uncomment for one time login in ne device ERRREZ
            # usersession = UserSession.objects.filter(user=user)
            # # print(usersession, 'salseman session')
            # if len(usersession)>0:
            #      # If the user is already authenticated, log them out
            #      print('user already post methode using class usersession')
            #      return redirect('main:login')
            # print('check if active')
            if user.is_active:
                # ERRREZ
                #UserSession.objects.create(user=user)
                print('user is active')
                login(request, user)
                request.session.set_expiry(30 * 24 * 60 * 60)
                # make user always connected finish this
                return redirect('main:catalogpage')
            else:
                print('user is not active')
                return redirect ('main:login')
        elif group=='clients':
            # get session of this user using django's default session management
            #uncomment for one device ERRREZ
            # usersession = UserSession.objects.filter(user=user)
            # print(usersession, 'client session')
            # if len(usersession)>0:
            #     # If the user is already authenticated, log them out
            #     print('user already post methode using class usersession')
            #     return redirect('main:login')
            if user.is_active:
                login(request, user)
                request.session.set_expiry(30 * 24 * 60 * 60)
                #onedevice ERRREZ
                #UserSession.objects.create(user=user)
                # keep user loged in
                print('user is active')
                return redirect('main:clientshome')
            else:
                print('user is not active')
                return redirect ('main:login')
        elif group == 'accounting':
            return redirect('main:orders')
        # elif group == 'admin':
        #     login(request, user)
        #     return redirect('main:ibra')
    else:
        return redirect('main:login')
    


@csrf_exempt
def editinfoclient(request):
    client=Client.objects.get(user_id=request.user.id)
    print(client.name)
    client.name=request.POST.get('name').strip()
    client.phone=request.POST.get('phone').strip()
    client.address=request.POST.get('address').strip()
    client.city=request.POST.get('city').strip()
    client.save()
    return redirect(profile)

@login_required(login_url='/login')
@csrf_exempt
def updatepassword(request):
    user=User.objects.get(pk=request.user.id)
    print(request.user.id)
    user.set_password(request.POST.get('cpass'))
    user.save()
    login(request, user)
    return redirect(profile)







@user_passes_test(tocatalog, login_url='main:loginpage')
@login_required(login_url='main:loginpage')
def commande(request):
    client=Client.objects.get(pk=request.POST.get('client'))
    # clientname=request.POST.get('clientname')
    # clientaddress=request.POST.get('clientaddress')
    # clientphone=request.POST.get('clientphone')
    cart=Cart.objects.filter(user=request.user).first()
    if cart and cart.total > 0:
        cartitems=Cartitems.objects.filter(cart=cart)
        itemsdisponible=[]
        itemsnotdisponible=[]
        totalofdispounible=0
        totalofnotdispounible=0
        for i in cartitems:
            if request.user.groups.first().name=='clients':
                if i.product.stocktotal>0:
                    totalofdispounible+=round(i.product.sellprice * i.qty, 2)
                    item={
                        'ref':i.product.ref,
                        'name':i.product.name,
                        'qty':i.qty,
                        'price':i.product.sellprice,
                        'total':round(i.product.sellprice * i.qty, 2),
                        'remise':i.product.remise,
                        'productid':i.product.id,
                        'uniqcode':i.product.uniqcode
                    }
                    itemsdisponible.append(item)
                    i.delete()
                # else:
                #     totalofnotdispounible+=i.total
                cart.total=totalofnotdispounible
                cart.save()
                
            else:
                if i.product.stocktotal>0:
                    totalofdispounible+=round(i.product.sellprice * i.qty, 2)
                    item={
                        'ref':i.product.ref,
                        'name':i.product.name,
                        'qty':i.qty,
                        'price':i.product.sellprice,
                        'total':round(i.product.sellprice * i.qty, 2),
                        'remise':i.product.remise,
                        'productid':i.product.id,
                        'uniqcode':i.product.uniqcode
                    }
                    itemsdisponible.append(item)
                    i.delete()
                else:
                    totalofnotdispounible+=round(i.product.sellprice * i.qty, 2)
                    item={
                        'ref':i.product.ref,
                        'name':i.product.name,
                        'qty':i.qty,
                        'price':i.product.sellprice,
                        'total':round(i.product.sellprice * i.qty, 2),
                        'remise':i.product.remise,
                        'uniqcode':i.product.uniqcode,
                        'productid':i.product.id,
                    }
                    itemsnotdisponible.append(item)
                    i.delete()
                cart.total=0
                cart.save()
        if request.user.groups.first().name=='clients' and totalofdispounible == 0:
            return JsonResponse({
                'valid':False,
                'message': 'Stock null panier'
            })
        notesorder=request.POST.get('notesorder')
        cmndfromclient=request.POST.get('cmndfromclient')
        if cmndfromclient == 'true':
            order=Order.objects.create(client=client, salseman=client.represent,  modpymnt='--', modlvrsn='--',total=totalofdispounible, isclientcommnd=True, note=notesorder, senttoserver=False)
            for i in itemsdisponible:
                Orderitem.objects.create(order=order, ref=i['ref'], name=i['name'], qty=int(i['qty']), product_id=i['productid'], remise=i['remise'], price=i['price'], total=i['total'])
            # try:
            #     req.get('http://localserver/commandfromserver', {'items':json.dumps(itemsdisponible), 'clientcode':client.code, 'total':totalofdispounible, 'notesorder':notesorder, 'cmndfromclient':cmndfromclient, 'userid':request.user.id})
            # except:
            #     order.senttoserver=False
            #     order.save()
            # async def send_message_to_group(group_chat_id, message_text):
            #     await bot.send_message(chat_id=group_chat_id, text=message_text)
            # # Initialize the bot
            # bot = telegram.Bot(token=TOKEN)
            # message_text = 'Nouveau commande server'

            # # Send message to the group
            # asyncio.run(send_message_to_group(group_chat_id, message_text))
        else:
            rep=Represent.objects.get(user_id=request.user.id).id
            order=Order.objects.create(client_id=request.POST.get('client'), salseman_id=rep,  modpymnt='--', modlvrsn='--',total=totalofdispounible, note=notesorder, senttoserver=False)
            for i in itemsdisponible:
                Orderitem.objects.create(order=order, ref=i['ref'], name=i['name'], qty=int(i['qty']), product_id=i['productid'], remise=i['remise'], price=i['price'], total=i['total'])
            # try:
            #     req.get('http://localserver/commandfromserver', {'items':json.dumps(itemsdisponible), 'clientcode':client.code, 'total':totalofdispounible, 'notesorder':notesorder, 'cmndfromclient':cmndfromclient, 'userid':request.user.id, 'rep':rep})
            # except:
            #     order.senttoserver=False
            #     order.save()
            if len(itemsnotdisponible)>0:
                reliquatorder=Order.objects.create(client_id=request.POST.get('client'), salseman_id=rep,  modpymnt='--', modlvrsn='--',total=totalofnotdispounible, note=notesorder+' Reliquat', senttoserver=False)
                for i in itemsnotdisponible:
                    Orderitem.objects.create(order=reliquatorder, ref=i['ref'], name=i['name'], qty=int(i['qty']), product_id=i['productid'], remise=i['remise'], price=i['price'], total=i['total'])
                # try:
                #     req.get('http://localserver/commandfromserver', {'items':json.dumps(itemsnotdisponible), 'clientcode':client.code, 'total':totalofnotdispounible, 'notesorder':notesorder+' Reliquat', 'cmndfromclient':cmndfromclient, 'userid':request.user.id, 'rep':rep})
                # except:
                #     order.senttoserver=False
                #     order.save()
                #     async def send_message_to_group(group_chat_id, message_text):
                #         await bot.send_message(chat_id=group_chat_id, text=message_text)
                #     # Initialize the bot
                #     bot = telegram.Bot(token=TOKEN)
                #     message_text = 'Nouveau commande server'
    
                #     # Send message to the group
                #     asyncio.run(send_message_to_group(group_chat_id, message_text))

        # Ordersnotif.objects.create(user_id=request.user.id)
        bot_token='7266453006:AAG-MvJL1LYYH26tK-9TjRVpLMWTsPNhwB0'
        chat_id='-555555'
        send_message_url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
        params = {
            'chat_id': chat_id,
            'text': f'client: {client.name}, representant: {client.represent} => {"Non" if cmndfromclient else "Oui"}, total: {order.total}'
        }
        response = req.get(send_message_url, params=params)
        if response.status_code == 200:
            print('Message sent successfully!')
        else:
            print('Failed to send message:', response.text)

        # totalremise=request.POST.get('totalremise', 0)
        
    # send_mail(message='Nouveau commande.', subject=f'Nouveau commande. #{order.id}')
    #threading.Thread(target=send_mail, args=('Nouveau commande.', f'Nouveau commande. #{order.id}', 'abdelwahedaitali@gmail.com', ['aitaliabdelwahed@gmail.com'], False)).start()
        return JsonResponse({
            'valid':True,
            'message':'Commande enregistrée avec succès',
        })
    else:
        print('no cart')
        return JsonResponse({
            'valid':False,
            'message':'Panier vide'
        })

# finish this userisclient
@user_passes_test(isclient, login_url='main:loginpage')
@login_required(login_url='main:loginpage')
def clientdashboar(request):
    # get id of request user
    id=request.user.id
    client=Client.objects.get(user_id=id)
    orders=Order.objects.filter(client=client, isdelivered=False)
    livraisons=Bonlivraison.objects.filter(client=client)
    ctx={
        'title':'Dashboard Client',
        'orders':orders,
        'livraisons':livraisons,
        'soldbl':client.soldbl,
        'soldfacture':client.soldfacture,
        'soldtotal':client.soldtotal,
    }
    return render(request, 'clientdashboar.html', ctx)


@user_passes_test(isaccounting, login_url='main:loginpage')
@login_required(login_url='main:loginpage')
def orders(request):
    # get orders from db and order them by date ascendant
    orders=Order.objects.all()
    delivered=len(Order.objects.all().filter(isdelivered=True))
    paied=len(Order.objects.all().filter(ispaied=True))
    #return JsonResponse({
    #     'data':render(request, 'orders.html', {'orders':orders, 'delivered':delivered, 'title':'Commandes', 'notdel':len(orders)-delivered, 'paied':paied})
    # })
    return render(request, 'orders.html', {'orders':orders, 'delivered':delivered, 'title':'Commandes', 'notdel':len(orders)-delivered, 'paied':paied})


def searchclient(request):
    term=request.GET.get('term')
    print(term)
    if '+' in term:
        term=term.split('+')
        for i in term:
            clients=Client.objects.filter(
                Q(name__icontains=i) |
                Q(code__icontains=i) |
                Q(region__icontains=i) |
                Q(city__icontains=i)
            )
    else:
        clients=Client.objects.filter(
            Q(name__icontains=term) |
            Q(code__icontains=term) |
            Q(region__icontains=term) |
            Q(city__icontains=term)
        )
    results=[]
    for i in clients:
        results.append({
            'id':i.id,
            'text':i.name
        })
    return JsonResponse({'results': results})


def orderitems(request, id):
    orderitems=Orderitem.objects.filter(order=id)
    order=Order.objects.get(pk=id)
    return JsonResponse({
        'data':render(request, 'orderitems.html', {'orderitems':orderitems, 'order':order}).content.decode('utf-8')
    })


def dilevered(request, id):
    order=Order.objects.get(pk=id)
    order.isdelivered=True
    order.save()
    return redirect('main:orders')

def paied(request, id):
    order=Order.objects.get(pk=id)
    order.ispaied=True
    order.save()
    return redirect('main:orders')


# gets products after clicking on a category
@user_passes_test(tocatalog, login_url='main:loginpage')
@login_required(login_url='main:loginpage')
def products(request, id):
    # get the products from the db
    c=Mark.objects.get(pk=id)
    products=Produit.objects.filter(mark_id=id)
    newproducts=Produit.objects.filter(isnew=True)
    ctx={'products':products, 
         'title':'Produits de '+str(c), 
         'category':c,
         'newproducts':newproducts}
    return render(request, 'products.html', ctx)

@user_passes_test(tocatalog, login_url='main:loginpage')
@login_required(login_url='main:loginpage')
def productscategories(request, id):
    # get the products from the db
    c=Category.objects.get(pk=id)
    
    products=Produit.objects.filter(category_id=id, isactive=True).order_by('code')
    # get group of the request user
    newproducts=Produit.objects.filter(isnew=True)
    nested_products = [[products[i], products[i+1]] for i in range(0, len(products)-1, 2)]

    # Create a final list by grouping pairs into sublists
    result = [nested_products[i:i+2] for i in range(0, len(nested_products), 2)]
    
    group=request.user.groups.first().name
    if group=='salsemen':
        if request.user.represent in c.excludedrep.all():
            products=[]
        else:
            if c.affichage=='double':
                print('>>>>>>>>><<double')
                products=[products[i:i+8] for i in range(0, len(products), 8)]
                print('>>>>>>>>><<double', products)
            else:
                products=[products[i:i+4] for i in range(0, len(products), 4)]
    elif group=='clients':
        if c.masqueclients:
            products=[]
    ctx={
            'products':products, 
            'title':'Produits de '+str(c), 
            'category':c,
            'newproducts':newproducts,
            'nextctg' : Category.objects.filter(code__gt=c.code).order_by('code').first(),
            'previousctg' : Category.objects.filter(code__lt=c.code).order_by('-code').first() 
        }
    return render(request, 'products.html', ctx)

@user_passes_test(tocatalog, login_url='main:loginpage')
@login_required(login_url='main:loginpage')
def productsmarks(request, id):
    # get the products from the db
    c=Mark.objects.get(pk=id)
    products=Produit.objects.filter(mark_id=id).order_by('code')
    newproducts=Produit.objects.filter(isnew=True)

    group=request.user.groups.first().name
    if group=='salsemen':
        products=[products[i:i+5] for i in range(0, len(products), 5)]
    ctx={'products':products, 
         'title':'Produits de '+str(c), 
         'category':c,
         'newproducts':newproducts}
    return render(request, 'markspdcts.html', ctx)

@user_passes_test(isadmin, login_url='main:loginpage')
@login_required(login_url='main:loginpage')
def ibra(request):
    client_ip = request.META.get('REMOTE_ADDR')
    print('>>>>>>>>>', client_ip)
    ctx={
        'title':'Dashboard',
        'orders':Order.objects.filter(date__date=datetime.date.today()).count(),
        'products':Produit.objects.all().count(),
        'productthismonth':Orderitem.objects.filter(order__date__month=datetime.date.today().month).order_by('-qty')[:20],
        'alerts':Produit.objects.filter(stocktotal__lte=F('minstock')).count(),
        'blnotpaid':Bonlivraison.objects.filter(ispaid=False).count(),
        'boncommand':Order.objects.filter(isdelivered=False).count(),
        'soldtotal':round(Client.objects.aggregate(Sum('soldtotal'))['soldtotal__sum'] or 0, 2),



    }
    return render(request, 'dashboard.html', ctx)

@user_passes_test(tocatalog, login_url='main:loginpage')
@login_required(login_url='main:loginpage')
def catalog(request):
    # categories = Category.objects.annotate(
    #     has_promotion=Exists(Produit.objects.filter(category_id=OuterRef('pk'), isoffer=True)),
    #     total_products=Count('produit')
    # )
    
    constraction=False
    if constraction:
        return render(request, 'constraction.html', {'title':'Under Constraction'})
    
    productslen=len(Produit.objects.all())
    marks = Mark.objects.annotate(
        has_promotion=Exists(Produit.objects.filter(mark_id=OuterRef('pk'), isoffer=True)),
        total_products=Count('produit')
    )
    categories = Category.objects.all().order_by('code').annotate(
        has_promotion=Exists(Produit.objects.filter(mark_id=OuterRef('pk'), isoffer=True)),
        total_products=Count('produit')
    )
    print('>>>>>',Produit.objects.filter(isnew=True))
    ctx={
            'categories': categories,
            'clients':Client.objects.all(),
            'title':'Catalog',
            'marques':marks,
            'productslen':productslen,
            'promotions':Promotion.objects.all(),
            'newproducts':Produit.objects.filter(isnew=True)
        }
    return render(request, 'searchpage.html', ctx)


@user_passes_test(tocatalog, login_url='main:loginpage')
@login_required(login_url='main:loginpage')
def catalogpage(request):
    # categories = Category.objects.annotate(
    #     has_promotion=Exists(Produit.objects.filter(category_id=OuterRef('pk'), isoffer=True)),
    #     total_products=Count('produit')
    # )
    
    constraction=False
    if constraction:
        return render(request, 'constraction.html', {'title':'Under Constraction'})
    
    request.session.set_expiry(30 * 24 * 60 * 60)
    productslen=len(Produit.objects.all())
    marks = Mark.objects.annotate(
        has_promotion=Exists(Produit.objects.filter(mark_id=OuterRef('pk'), isoffer=True)),
        total_products=Count('produit')
    )
    categories = Category.objects.all().order_by('code').annotate(
        has_promotion=Exists(Produit.objects.filter(mark_id=OuterRef('pk'), isoffer=True)),
        total_products=Count('produit')
    )
    ctx={
            'categories': categories,
            'firstctg':Category.objects.order_by('code').first(),
            'clients':Client.objects.all(),
            'title':'Catalog',
            'marques':marks,
            'productslen':productslen,
            'promotions':Promotion.objects.all()
        }
    return render(request, 'catalog.html', ctx)

@user_passes_test(bothsalseaccount, login_url='main:loginpage')
@login_required(login_url='main:loginpage')
def ordersforeach(request):
    # get id of request user
    id=request.user.id
    rep=Represent.objects.get(user_id=id)
    orders=Order.objects.filter(isclientcommnd=False).filter(salseman=rep)
    delivered=len(orders.filter(isdelivered=True))
    paied=len(orders.filter(ispaied=True))
    total=Order.objects.exclude(note__icontains='Reliquat')
    return render(request, 'orders.html', {'orders':orders, 'delivered':delivered, 'title':'Commandes', 'notdel':len(orders)-delivered, 'paied':paied, 'total':orders.exclude(note__icontains='Reliquat').aggregate(Sum('total'))['total__sum'] or 0})
@user_passes_test(bothsalseaccount, login_url='main:loginpage')
@login_required(login_url='main:loginpage')
def salsemanorders(request, str_id):
    orders=Order.objects.get(code=str_id)
    items=Orderitem.objects.filter(order=orders.id)
    return render(request, 'salsemanorders.html', {'order':orders, 'items':items, 'title':'Commande #'+str(orders.id)})




def clients(request):
    clients=Client.objects.all()
    # Convert the QuerySet to a list of dictionaries
    data = list(clients.values())

    # Serialize the list as JSON
    json_data = json.dumps(data)
    # return a json response with clients as clients
    return JsonResponse({
        'clients':json_data
    })


def addclient(request):
    name=request.POST.get('name')
    phone=request.POST.get('phone')
    address=request.POST.get('address')
    city=request.POST.get('city')
    ice=request.POST.get('ice')
    rep=Represent.objects.get(user_id=request.user.id)
    try:
        lastcode = Client.objects.last()
        print('lastcode', lastcode.code)
        if lastcode:
            
            codecl = f"{int(lastcode.code) + 1:06}"
        else:
            codecl = f"000001"
    except:
        codecl="000001"
    
    Client.objects.create(name=name, phone=phone, address=address, city=city, ice=ice, code=codecl, represent=rep)
    options=['<option value="'+str(i.id)+'">'+i.code+' | '+i.name+' | '+i.city+'</option>' for i in Client.objects.all().order_by('-id')]
    print(options)
    return JsonResponse({
        'options':options,
    })

def logoutuser(request):
    logout(request)
    return redirect('main:loginpage')


def aboutus(request):
    return render(request, 'aboutus.html', {'title':'A propos de nous'})


@user_passes_test(tocatalog, login_url='main:loginpage')
def cart(request):
    clients=Client.objects.all()
    return render(request, 'cart.html', {'title':'Panier', 'clients':clients})

def developer(request):
    return render(request, 'me.html', {'title':'Develper - abdelwahed ait ali'})

# def signup(request):
#     if request.method == 'POST':
#         name=request.POST.get('name')
#         email=request.POST.get('email')
#         password=request.POST.get('password')
#         usename=request.POST.get('usename')
        
#         return redirect('loginpage')


def sitemap(request):
    # Get the base URL for the sitemap
    host_base = request.build_absolute_uri(reverse("main:home"))

    # Static routes with static content
    static_urls = []
    for url in ["#","login"]:
        static_urls.append({"loc": f"{host_base}{url}"})

    # Render the sitemap template
    context = {"static_urls": static_urls}
    sitemap_xml = render(request, "sitemap.xml", context, content_type="application/xml")

    # Return the sitemap as an HTTP response with the appropriate content type
    return HttpResponse(sitemap_xml, content_type="application/xml")


def makeuserconnected(request):
    if not (request.user.groups.all()[0].name=='admin'):
        try:
            useralready=Connectedusers.objects.get(user=request.user)
            useralready.activity=request.GET.get('activity')
            useralready.lasttime=timezone.now()
            useralready.save()
        except:
            Connectedusers.objects.create(user=request.user, activity=request.GET.get('activity'))
        print('user connecte')
    return JsonResponse({
        'success':True
    })

# search global will be for client search , like search ref, but its gonne be ajax request
def searchglobal(request):
    ref=request.GET.get('term')
    products = Produit.objects.filter(Q(ref__icontains=ref) | Q(name__icontains=ref) | Q(cars__icontains=ref) | Q(coderef__icontains=ref) | Q(equivalent__icontains=ref) | Q(refeq1__icontains=ref) | Q(refeq2__icontains=ref) | Q(refeq3__icontains=ref) | Q(refeq4__icontains=ref) | Q(diametre__icontains=ref) | Q(coderef__icontains=ref))
    
    return JsonResponse({'html': render(request, 'clientproductsearch.html', {'products':products}).content.decode('utf-8')})

def productdata(request):
    id=request.GET.get('id')
    product=Produit.objects.get(pk=id)
    ctx={'product':product}
    if product.cars is not None:
        cars=json.loads(product.cars)
        ctx['cars']=cars
    return JsonResponse({
        'html':render(request, 'productdata.html', ctx).content.decode('utf-8'),
        # 'name':product.name,
        # 'price':product.price,
        # 'offre':product.offre,
        # 'min':product.min,
        # 'ref':product.ref,
        # 'category':product.category.title,
        # 'category_id':product.category.id,
        # 'brand':product.brand,
        # 'model':product.model,
        # 'mark':product.mark.name,
        # 'mark_id':product.mark.id,
        # 'image':product.image.url,
        # 'stocktotal':product.stocktotal,
        # 'stock':product.stock,
        # 'isoffer':product.isoffer,
        # 'isnew':product.isnew,
        # 'isactive':product.isactive,
        # 'cars':product.cars,
        # 'coderef':product.coderef,
        # 'equivalent':product.equivalent,
        # 'refeq1':product.refeq1,
        # 'refeq2':product.refeq2,
        # 'refeq3':product.refeq3,
        # 'refeq4':product.refeq4,
        # 'diametre':product.diametre,
    })
def addtocart(request):
    # use try except cause the cart may noto be created
    productid=request.GET.get('productid')
    qty=request.GET.get('qty')
    print('>>>>>>>>>', productid, qty)
    product=Produit.objects.get(pk=productid)
    total=round(int(qty)*product.sellprice, 2)
    #group=request.user.groups.all().first().name
    #if group == 'clients':
    #    total=round(int(qty)*product.prixnet, 2)
    #elif group == 'salsemen':
    #    if product.representprice > 0:
    #        total=round(int(qty)*product.representprice, 2)
    #    else:
    #        total=round(int(qty)*product.prixnet, 2)
    cart=Cart.objects.filter(user=request.user).first()
    if cart:
        # check if product alrady exist
        exist=Cartitems.objects.filter(cart=cart, product=product).first()
        if exist:
            cart.total=round(cart.total-exist.total+total, 2)
            cart.save()
            exist.qty=qty
            exist.total=total
            exist.save()
            print('>>>>>>> item already')
            return JsonResponse({
                'success':False,
                'message':'Produit commandé deja'
            })
        else:
            # if not update total and create item in the same cart
            cart.total=round(cart.total+total, 2)
            Cartitems.objects.create(cart=cart, product=product, qty=qty, total=total)
            cart.save()
    else:
        #print('Exception, in addtocart', e)
        cart=Cart.objects.create(user=request.user, total=total)
        Cartitems.objects.create(cart=cart, product=product, qty=qty, total=total)
    return JsonResponse({
        'success':True
        })
def removeitemfromcart(request):
    productid=request.GET.get('productid')
    

    product=Produit.objects.get(pk=productid)
    cart=Cart.objects.get(user=request.user)
    itemtoremove=Cartitems.objects.filter(cart=cart, product=product).first()

    cart.total=round(cart.total-itemtoremove.total, 2)
    cart.save()
    itemtoremove.delete()
    return JsonResponse({
        'success':True
    })
def removecart(request):
    cart=Cart.objects.get(user=request.user)
    cart.delete()
    return JsonResponse({
        'success':True
    })

def getitemsincart(request):
    length=0
    itemscart=[]
    userid=request.GET.get('userid')
    print('>>>>>', userid)
    try:
        cart=Cart.objects.get(user_id=userid)
        items=Cartitems.objects.filter(cart=cart).order_by('-id')
        length=len(items)
        for i in items:
            if i.product.stocktotal<=0:
                status="indisponible"
            elif i.product.stocktotal>=5:
                status="disponible"
            else:
                status="soon"
            itemscart.append({
                'cartid':cart.id,
                'cartitemid':i.id,
                'ref':i.product.ref,
                'name':i.product.name,
                'remise':i.product.remise,
                'image':i.product.image.url if i.product.image else '',
                'sellprice':i.product.sellprice,
                'qty':i.qty,
                'id':i.product.id,
                'status':status
            })
    except:
        pass
    response= JsonResponse({
        'length':length,
        'items':itemscart
    })
    response['Access-Control-Allow-Origin'] = 'http://localserver'
    return response

def updateproduct(request):
    id=request.GET.get('id')
    product=Produit.objects.get(pk=id)
    product.stocktotal=request.GET.get('stocktotal')
    product.save()
    return JsonResponse({
        'success':True
    })

def addtowhishlist(request):
    # use try except cause the cart may noto be created
    productid=request.GET.get('productid')
    qty=request.GET.get('qty')
    print('>>>>>>>>>', productid, qty)
    product=Produit.objects.get(pk=productid)
    total=round(int(qty)*product.sellprice, 2)
    try:
        cart=Wich.objects.get(user=request.user)
        # check if product alrady exist
        exist=Wishlist.objects.filter(wich=cart, product=product)
        if exist:
            print('>>>>>>> item already')
            return JsonResponse({
                'success':False,
                'message':'Produit commandé deja'
            })
        else:
            # if not update total and create item in the same cart
            cart.total=round(cart.total+total, 2)
            Wishlist.objects.create(wich=cart, product=product, qty=qty, total=total)
            cart.save()
    except Exception as e:
        print('Exception, in addtocart', e)
        cart=Wich.objects.create(user=request.user, total=total)
        Wishlist.objects.create(wich=cart, product=product, qty=qty, total=total)
    return JsonResponse({
        'success':True
        })

def updatecartitem(request):
    qty=request.GET.get('qty')
    productid=request.GET.get('productid')
    cartid=request.GET.get('cartid')
    cartitemid=request.GET.get('cartitemid')
    cart=Cart.objects.get(pk=cartid)
    product=Produit.objects.get(pk=productid)
    item=Cartitems.objects.get(pk=cartitemid)
    cart.total=round(float(cart.total)-float(item.total), 2)
    item.qty=qty
    total=round(float(product.sellprice)*float(qty), 2)
    cart.total=cart.total+total
    item.total=total
    item.save()
    cart.save()
    return JsonResponse({
        'success':True
    })

def updatewishitem(request):
    qty=request.GET.get('qty')
    productid=request.GET.get('productid')
    cartid=request.GET.get('cartid')
    cartitemid=request.GET.get('cartitemid')
    cart=Wich.objects.get(pk=cartid)
    product=Produit.objects.get(pk=productid)
    item=Wishlist.objects.get(pk=cartitemid)
    cart.total=round(float(cart.total)-float(item.total), 2)
    item.qty=qty
    total=round(float(product.sellprice)*float(qty), 2)
    cart.total=cart.total+total
    item.total=total
    item.save()
    cart.save()
    return JsonResponse({
        'success':True
    })


def getitemsinwishlist(request):
    length=0
    itemswich=[]
    userid=request.GET.get('userid')
    print('>>>>>', userid)
    try:
        wich=Wich.objects.get(user_id=userid)
        print('>>>>', wich)
        items=Wishlist.objects.filter(wich=wich)
        length=len(items)
        for i in items:
            if i.product.stocktotal<=0:
                status="indisponible"
            elif i.product.stocktotal>=5:
                status="disponible"
            else:
                status="soon"
            itemswich.append({
                'wichid':wich.id,
                'wichitemid':i.id,
                'ref':i.product.ref,
                'name':i.product.name,
                'remise':i.product.remise,
                'image':i.product.image.url if i.product.image else '',
                'sellprice':i.product.sellprice,
                'qty':i.qty,
                'id':i.product.id,
                'status':status
            })
        print('>>>>>>>>> itemswich', itemswich, length)
    except:
        pass
    res= JsonResponse({
        'length':length,
        'items':itemswich
    })
    res['Access-Control-Allow-Origin'] = 'http://localserver'
    return res

def removeitemfromwish(request):
    print('>>>>>>> remove from wish')
    productid=request.GET.get('productid')
    

    product=Produit.objects.get(pk=productid)
    cart=Wich.objects.get(user=request.user)
    itemtoremove=Wishlist.objects.get(wich=cart, product=product)

    cart.total=round(cart.total-itemtoremove.total, 2)
    cart.save()
    itemtoremove.delete()
    return JsonResponse({
        'success':True
    })

def switchtocart(request):
    try:
        wich=Wich.objects.get(user=request.user)
        wichitems=Wishlist.objects.filter(wich=wich)
        cart=Cart.objects.filter(user=request.user).first()
        for i in wichitems:
            if i.product.stocktotal > 0:
                print('product in stock', i.product.ref, i.total)
                if cart:
                    Cartitems.objects.create(cart=cart, product=i.product, qty=i.qty, total=i.total)
                    cart.total=round(cart.total+i.total, 2)
                    cart.save()
                else:
                    cart=Cart.objects.create(user=request.user, total=i.total)
                    Cartitems.objects.create(cart=cart, product=i.product, qty=i.qty, total=i.total)
                    
                i.delete()
        return JsonResponse({
            'success':True
        })
    except Exception as e:
        print('>>error in switch to cart', e)
        return JsonResponse({
            'success':True
        })

@user_passes_test(tocatalog, login_url='main:loginpage')
def replicata(request):
    return render(request, 'replicata.html', {'title':'Reliquat'})

def notifications(request):
    notifications=Notification.objects.all()
    return JsonResponse({
        'notifications':list(notifications.values()),
        'length':notifications.count()
    })
def catalogpermission(request):
    password=request.GET.get('password')
    if password and password=='0000':
        firstctgid=Category.objects.order_by('code').first().id
        return JsonResponse({
            'success':True,
            'url':f'/categories/products/{firstctgid}'
        })
    else:
        return JsonResponse({
            'success':False,
            'error':'Mot de passe incorrect'
        })

def newarrivage(request):
    info=request.GET.get('info') or  'ee'
    category=info.split()
    if len(category)>1:
        products=Produit.objects.filter(isnew=True).annotate(
        category_priority=Case(
            When(category__id=category[-1], then=Value(0)),  # The specified category first
            default=Value(1),  # Other categories next
            output_field=IntegerField(),
            )
        ).order_by('category_priority', '-stocktotal')
    else:
        products=Produit.objects.filter(isnew=True).order_by('-stocktotal')
    ctx={
        'products':products, 
        'title':'Produits de nouvau arrivage', 
        'arrivage':True
    }
    #return 
    #return JsonResponse({'html':render(request, 'products.html', ctx)})
    return render(request, 'products.html', ctx)
def allproducts(request):
    products=Produit.objects.all().order_by('category__code').order_by('code')
    nested_products = [[products[i], products[i+1]] for i in range(0, len(products)-1, 2)]

    # Create a final list by grouping pairs into sublists
    result = [nested_products[i:i+2] for i in range(0, len(nested_products), 2)]
    
    group=request.user.groups.first().name
    if group=='salsemen':
        products=[products[i:i+4] for i in range(0, len(products), 4)]
    ctx={
        'products':products
    }
    return render(request, 'products.html', ctx)

def ordersnotsent(request):
    orders=Order.objects.filter(senttoserver=False)
    ctx={
        'orders':orders
    }
    return render(request, 'notsent.html', ctx)

def sendordertoserver(request):
    orderid=request.GET.get('orderid')
    order=Order.objects.get(pk=orderid)
    orderitems=Orderitem.objects.filter(order=order)
    itemsdisponible=[]
    for i in orderitems:
        item={
            'ref':i.product.ref,
            'name':i.product.name,
            'qty':i.qty,
            'price':i.product.sellprice,
            'total':i.total,
            'remise':i.product.remise,
            'productid':i.product.id,
            'uniqcode':i.product.uniqcode,
        }
        itemsdisponible.append(item)
    try:
        req.get('http://localserver/commandfromserver', {'items':json.dumps(itemsdisponible), 'clientcode':order.client.code, 'total':order.total, 'notesorder':order.note, 'cmndfromclient':'true' if order.isclientcommnd else 'false', 'rep':order.client.represent.id if order.client.represent else None, 'userid':1})
        order.senttoserver=True
        order.save()
        return JsonResponse({
            'success':True
        })
    except Exception as e:
        order.senttoserver=False
        order.save()
        return JsonResponse({
            'success':False,
            'error':f'error>> {e}'
        })

def workingclient(request):
    rep=request.user.represent
    clientid=request.GET.get('clientid')
    rep.client_id=clientid
    rep.save()
    return JsonResponse({
        'success':True
    })

def relveclientforrep(request):
    if request.user.represent.caneditprice:
        return render(request, 'situationcl.html', {'today':timezone.now().date()})
    return redirect('main:catalogpage')

def getproducdataforsuppliers(request):
    html=req.get(f"http://167.71.77.64/searcher/getproducdataforsuppliers?code={request.GET.get('code')}").content.decode('utf-8')
    return JsonResponse({
        'html':html
    })


        
