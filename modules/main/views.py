from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate

# Create your views here.
@login_required(login_url="/login")
def homepage(request):
    return render(request = request,
                  template_name='main/home.html')


def login_request(request):
    # Check if the user is already authenticated
    if request.user.is_authenticated:
        return redirect('/')  # Redirect to homepage if logged
    
    if request.method == 'POST':
        username = request.POST.get("username")
        password = request.POST.get("password")
        
        try:
            user = authenticate(username=username, password=password)

        except:
            messages.error(request, "User Not Found....")
            return redirect("login")

        if user is not None:
            login(request, user)
            messages.info(request, f"You are now logged in as {username}")
            return redirect('homepage')
        else:
            messages.error(request, "Invalid username or password.")

    return render(request = request,
                    template_name = "registration/login.html")


def logout_request(request):
    logout(request)
    messages.info(request, "Logged out successfully!")
    return redirect("login")
