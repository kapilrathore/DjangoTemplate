try:
    from urllib import quote_plus #python 2
except:
    pass

# try:
#     from urllib.parse import quote_plus #python 3
# except: 
#     pass

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

from django.core.urlresolvers import reverse

from comments.forms import CommentForm
from comments.models import Comment
from accounts.models import Friend
from .forms import PostForm
from .models import Post


@login_required
def post_create(request):
		
	form = PostForm(request.POST or None, request.FILES or None)
	if form.is_valid():
		instance = form.save(commit=False)
		instance.user = request.user
		instance.save()
		# message success
		messages.success(request, "Successfully Created")
		url = reverse("posts:list")
		return HttpResponseRedirect(url)
	context = {
		"form": form,
	}
	return render(request, "post_form.html", context)

def post_detail(request, slug=None):
	instance = get_object_or_404(Post, slug=slug)
	if instance.draft:
		if instance.user != request.user:
			raise Http404

	initial_data = {
			"content_type": instance.get_content_type,
			"object_id": instance.id
	}
	form = CommentForm(request.POST or None, initial=initial_data)
	if form.is_valid() and request.user.is_authenticated():
		c_type = form.cleaned_data.get("content_type")
		content_type = ContentType.objects.get(model=c_type)
		obj_id = form.cleaned_data.get('object_id')
		content_data = form.cleaned_data.get("content")
		parent_obj = None
		try:
			parent_id = int(request.POST.get("parent_id"))
		except:
			parent_id = None

		if parent_id:
			parent_qs = Comment.objects.filter(id=parent_id)
			if parent_qs.exists() and parent_qs.count() == 1:
				parent_obj = parent_qs.first()


		new_comment, created = Comment.objects.get_or_create(
							user = request.user,
							content_type= content_type,
							object_id = obj_id,
							content = content_data,
							parent = parent_obj,
						)
		return HttpResponseRedirect(new_comment.content_object.get_absolute_url())


	comments = instance.comments
	context = {
		"title": instance.title,
		"instance": instance,
		"comments": comments,
		"comment_form":form,
	}
	return render(request, "post_detail.html", context)

@login_required
def post_list(request):
	
	today = timezone.now().date()

	queryset_list = []

	if request.user.is_superuser:
		posts = Post.objects.all()
		for post in posts:
			queryset_list.append(post)
	
	else:
		posts = Post.objects.filter(user = request.user)
		for post in posts:
			queryset_list.append(post)

		friend = Friend.objects.get(current_user=request.user)
		users = friend.friends.all()

		for user in users:
			posts = Post.objects.active().filter(user = user)
			for post in posts:
				queryset_list.append(post)

	context = {
		"object_list": queryset_list, 
		"title": "Feed",
		"today": today,
	}
	
	return render(request, "post_list.html", context)


def post_update(request, slug=None):
	if not request.user.is_staff or not request.user.is_superuser:
		raise Http404
	instance = get_object_or_404(Post, slug=slug)
	form = PostForm(request.POST or None, request.FILES or None, instance=instance)
	if form.is_valid():
		instance = form.save(commit=False)
		instance.save()
		messages.success(request, "<a href='#'>Item</a> Saved", extra_tags='html_safe')
		return HttpResponseRedirect(instance.get_absolute_url())

	context = {
		"title": instance.title,
		"instance": instance,
		"form":form,
	}
	return render(request, "post_form.html", context)



def post_delete(request, slug=None):
	if not request.user.is_staff or not request.user.is_superuser:
		raise Http404
	instance = get_object_or_404(Post, slug=slug)
	instance.delete()
	messages.success(request, "Successfully deleted")
	return redirect("posts:list")

@login_required
def post_verify(request, slug=None):
	
	instance = get_object_or_404(Post, slug=slug)

	if instance.user == request.user or request.user.is_superuser:
		return redirect('/')

	instance.my_photo = True
	instance.save()

	messages.success(request, "Verified and uploaded online. Thank you.")

	initial_data = {
		"content_type": instance.get_content_type,
		"object_id": instance.id
	}

	form = CommentForm(request.POST or None, initial=initial_data)
	if form.is_valid() and request.user.is_authenticated():
		c_type = form.cleaned_data.get("content_type")
		content_type = ContentType.objects.get(model=c_type)
		obj_id = form.cleaned_data.get('object_id')
		content_data = form.cleaned_data.get("content")
		parent_obj = None
		try:
			parent_id = int(request.POST.get("parent_id"))
		except:
			parent_id = None

		if parent_id:
			parent_qs = Comment.objects.filter(id=parent_id)
			if parent_qs.exists() and parent_qs.count() == 1:
				parent_obj = parent_qs.first()


		new_comment, created = Comment.objects.get_or_create(
							user = request.user,
							content_type= content_type,
							object_id = obj_id,
							content = content_data,
							parent = parent_obj,
						)
		return HttpResponseRedirect(new_comment.content_object.get_absolute_url())

	comments = instance.comments
	context = {
		"title": instance.title,
		"instance": instance,
		"comments": comments,
		"comment_form":form,
	}

	return render(request, "post_detail.html", context)