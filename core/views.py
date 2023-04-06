from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.models import User, auth
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Profile, Post, LikePost, FollowersCount
from itertools import chain
import random


@login_required(login_url='signin')
def index(request):
    user_object = User.objects.get(username=request.user.username)
    user_profile = Profile.objects.get(user=user_object)

    feed_list = []
    user_following = FollowersCount.objects.filter(follower=request.user.username) # only check the ones that we followed.

    user_following_list = [user.user for user in user_following]
    for usernames in user_following_list:
        feed_list += Post.objects.filter(user=usernames) # time reversed / add my own posts

    # posts = Post.objects.all()

    # user suggestion starts
    all_users = User.objects.all()
    user_following_all = [User.objects.get(username=user.user) for user in user_following]
    user_following_all.append(User.objects.get(username=request.user.username))
    new_suggestions = [x for x in list(all_users) if (x not in user_following_all)]

    if len(new_suggestions) > 5:
        new_suggestions = random.sample(new_suggestions, 5)
    else:
        random.shuffle(new_suggestions)

    username_profile = [users.id for users in new_suggestions]
    username_profile_list = []

    for ids in username_profile:
        profile_lists = Profile.objects.filter(id_user=ids)
        username_profile_list.append(profile_lists)

    suggestions_username_profile_list = list(chain(*username_profile_list))

    context = {
        'user_profile': user_profile,
        'posts': feed_list,
        'suggestions_username_profile_list': suggestions_username_profile_list
    }
    return render(request, 'index.html', context)


@login_required(login_url='signin')
def upload(request):

    if request.method == 'POST':
        user = request.user.username
        image = request.FILES.get('image_upload')
        caption = request.POST['caption']
        new_post = Post.objects.create(user=user, image=image, caption=caption)
        new_post.save()

    return redirect('/')


@login_required(login_url='signin')
def search(request):

    user_object = User.objects.get(username=request.user.username)
    user_profile = Profile.objects.get(user=user_object)

    username_profile_list = []
    if request.method == 'POST':
        username = request.POST['username']
        username_object = User.objects.filter(username__icontains=username)

        username_profile = []

        for users in username_object:
            username_profile.append(users.id)
        for ids in username_profile:
            profile_list = Profile.objects.filter(id_user=ids)
            username_profile_list.append(profile_list)
        username_profile_list = list(chain(*username_profile_list))

    return render(request, 'search.html', {'user_profile': user_profile, 'username_profile_list': username_profile_list})

@login_required(login_url='signin')
def settings(request):
    user_profile = Profile.objects.get(user=request.user)

    if request.method == 'POST':

        image = request.FILES.get('image')
        if image:
            user_profile.profileImg = image

        bio = request.POST['bio']
        location = request.POST['location']

        user_profile.bio = bio
        user_profile.location = location
        user_profile.save()

        return redirect('settings')

    return render(request, 'setting.html', {'user_profile': user_profile})


def signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        password2 = request.POST['password2']

        if password == password2:
            if User.objects.filter(email=email).exists():
                messages.info(request, 'Email Taken.')
                return redirect('signup')
            elif User.objects.filter(username=username).exists():
                messages.info(request, 'Username Taken.')
                return redirect('signup')
            else:  # create user successfully
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password
                )
                user.save()

                # log user in and redirect to settings page
                user_login = auth.authenticate(username=username, password=password)
                auth.login(request, user_login)

                # create a Profile object for the new user
                user_model = User.objects.get(username=username)
                new_profile = Profile.objects.create(user=user_model, id_user=user_model.id)
                new_profile.save()
                return redirect('settings')
        else:
            messages.info(request, 'Password Not Matching.')
            return redirect('signup')

    else:
        return render(request, 'signup.html')


def signin(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = auth.authenticate(username=username, password=password)
        if user:
            auth.login(request, user)
            return redirect('/')
        else:
            messages.info(request, 'Credentials Invalid')
            return redirect('signin')
    else:
        return render(request, 'signin.html')


@login_required(login_url='signin')
def profile(request, pk):
    user_object = User.objects.get(username=pk)
    user_profile = Profile.objects.get(user=user_object)
    user_posts = Post.objects.filter(user=pk)
    num_user_posts = len(user_posts)

    follower = request.user.username
    num_user_followers = len(FollowersCount.objects.filter(user=pk))
    num_user_following = len(FollowersCount.objects.filter(follower=pk))

    if FollowersCount.objects.filter(follower=follower, user=pk).first():
        button_text = 'Unfollow'
    else:
        button_text = 'Follow'

    context = {
        'user_object': user_object,
        'user_profile': user_profile,
        'user_posts': user_posts,
        'num_user_posts': num_user_posts,
        'button_text': button_text,
        'num_user_followers': num_user_followers,
        'num_user_following': num_user_following
    }
    return render(request, 'profile.html', context)

@login_required(login_url='signin')
def follow(request):

    if request.method == 'POST':
        follower = request.POST['follower']
        user = request.POST['user']

        if FollowersCount.objects.filter(follower=follower, user=user).first():
            delete_follower = FollowersCount.objects.get(follower=follower, user=user)
            delete_follower.delete()
        else:
            new_follower = FollowersCount.objects.create(follower=follower, user=user)
            new_follower.save()
        return redirect(f'profile/{user}')
    else:
        return redirect('/')

@login_required(login_url='signin')
def like_post(request):
    username = request.user.username
    post_id = request.GET.get('post_id')
    post = Post.objects.get(id=post_id)

    like_filter = LikePost.objects.filter(post_id=post_id, username=username).first()

    if not like_filter:
        new_like = LikePost.objects.create(post_id=post_id, username=username)
        new_like.save()
        post.num_likes += 1
        post.save()
    else:
        like_filter.delete()
        post.num_likes -= 1
        post.save()
    return redirect('/')


@login_required(login_url='signin')
def logout(request):
    auth.logout(request)
    return redirect('signin')
