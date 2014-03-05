from django.http import HttpResponse
from django.template import RequestContext
from django.shortcuts import render_to_response
from rango.models import Category
from rango.models import Page
from rango.forms import CategoryForm
from rango.forms import PageForm
from rango.forms import UserForm, UserProfileForm
from django.contrib.auth import authenticate, login
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout

def encode_url(str):
    return str.replace(' ', '_')

def decode_url(str):
    return str.replace('_', ' ')

def index(request):
    request.session.set_test_cookie()
    #return HttpResponse("Rango says fuck off! <a href='/rango/about'>About</a>")
    context = RequestContext(request)
    #context_dict = {'boldmessage': "I am the bold font from the context"}
    #return render_to_response('rango/index.html', context_dict, context)
    category_list = Category.objects.order_by('-likes')[:5] #- decending, 5 gives top 5
    context_dict = {'categories': category_list}

    for category in category_list:
        category.url = encode_url(category.name)

    page_list = Page.objects.order_by('-views')[:5]
    context_dict['pages'] = page_list
    return render_to_response('rango/index.html', context_dict, context)

def about(request):
    #return HttpResponse("This is about rango...<a href='/rango/'>Index</a>")
    context = RequestContext(request)
    context_dict = {'boldmessage': "this is about the bold font"}
    return render_to_response('rango/about.html', context_dict, context)

def category(request, category_name_url):
    context = RequestContext(request)

    category_name = decode_url(category_name_url)

    context_dict = {'category_name' : category_name, 'catergory_name_url': category_name_url}

    try:
        category = Category.objects.get(name=category_name)

        pages = Page.objects.filter(category=category)

        context_dict['pages'] = pages
        context_dict['category'] = category

    except Category.DoesNotExist:
        pass

    return render_to_response('rango/category.html', context_dict, context)

@login_required
def add_category(request):
    context = RequestContext(request)

    if request.method == 'POST':
        form = CategoryForm(request.POST)

        if form.is_valid():
            form.save(commit=True)
            return index(request)
        else:
            print form.errors

    else:
        form = CategoryForm()

    return render_to_response('rango/add_category.html', {'form': form}, context)

@login_required
def add_page(request, category_name_url):
    context = RequestContext(request)

    category_name = decode_url(category_name_url)
    if request.method == 'POST':
        form = PageForm(request.POST)

        if form.is_valid():
            page = form.save(commit=False)

            try:
                cat = Category.objects.get(name=category_name)
                page.category = cat
            except Category.DoesNotExist:
                return render_to_response('rango/add_category.html', {}, context)
            page.views = 0
            page.save()

            return category(request, category_name_url)
        else:
            print form.errors

    else:
        form = PageForm()

    return render_to_response( 'rango/add_page.html',
            {'category_name_url': category_name_url,
            'category_name': category_name, 'from': form},
            context)

def register(request):
    if request.session.test_cookie_worked():
        print ">>>> Test cookie worked!"
        request.session.delete_test_cookie()
    context = RequestContext(request)

    #boolean to indicate whether registration successful
    registered = False

    #post request => process data
    if request.method == 'POST':
        user_form = UserForm(data=request.POST)
        profile_form = UserProfileForm(data=request.POST)

        #forms valid
        if user_form.is_valid() and profile_form.is_valid():
            #save user's form to database
            user = user_form.save()

            #hash pw with set_pw, updatae user object
            user.set_password(user.password)
            user.save()

            #sort out userprofile insstance
            profile = profile_form.save(commit=False)
            profile.user = user

            #picture?
            if 'picture' in request.FILES:
                profile.picture = request.FILES['picture']

            #save userprof model instance
            profile.save()
            registered = True

    else:
        user_form = UserForm()
        profile_form = UserProfileForm()

    return render_to_response(
        'rango/register.html',
        {'user_form': user_form, 'profile_form': profile_form, 'registered': registered},
        context)

def user_login(request):
    context = RequestContext(request)

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                return HttpResponseRedirect('/rango/')
            else:
                context_dict['disabled_account'] = True
                return render_to_response('rango/login.html', context_dict, context)
        else:
            print "Invalid login details: {0}, {1}".format(username, password)
            context_dict['bad_details'] = True
            return  render_to_response('rango/login.html',context_dict, context)

    else:
        return render_to_response('rango/login.html', {}, context)

@login_required     #decorator!
def restricted(request):

    return HttpResponse("Since you're logged in, you can see this text!")

@login_required
def user_logout(request):
    logout(request)
    return HttpResponseRedirect('/rango/')
