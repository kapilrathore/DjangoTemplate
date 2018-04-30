from django.contrib.auth import (
    authenticate,
    get_user_model,
    login,
    logout,
    )

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from accounts.models import Friend

from .forms import UserLoginForm, UserRegisterForm

def login_view(request):
    print(request.user.is_authenticated())
    next = request.GET.get('next')
    title = "Login"
    form = UserLoginForm(request.POST or None)
    if form.is_valid():
        username = form.cleaned_data.get("username")
        password = form.cleaned_data.get('password')
        user = authenticate(username=username, password=password)
        login(request, user)
        if next:
            return redirect(next)
        return redirect("/")
    return render(request, "form.html", {"form":form, "title": title})


def register_view(request):
    print(request.user.is_authenticated())
    next = request.GET.get('next')
    title = "Register"
    form = UserRegisterForm(request.POST or None)
    if form.is_valid():
        user = form.save(commit=False)
        password = form.cleaned_data.get('password')
        user.set_password(password)
        user.save()
        
        friend = Friend.objects.create(current_user=user)
        friend.save()

        new_user = authenticate(username=user.username, password=password)
        login(request, new_user)
        if next:
            return redirect(next)
        return redirect("/")

    context = {
        "form": form,
        "title": title
    }
    return render(request, "form.html", context)

@login_required
def all_users(request):
    title = "All Users"
    
    all_users = User.objects.filter(is_superuser=False).exclude(id=request.user.id)
    friend = Friend.objects.get(current_user=request.user)
    friends = friend.friends.all()

    context = {
        "all_users": all_users,
        "friends": friends,
        "title": title
    }
    return render(request, "all_users.html", context)

def logout_view(request):
    logout(request)
    return redirect("/")

def change_friends(request, operation, pk):
    new_friend = User.objects.get(pk=pk)
    if operation == 'add':
        Friend.make_friend(request.user, new_friend)
    elif operation == 'remove':
        Friend.remove_friend(request.user, new_friend)

    return redirect("/all_users")