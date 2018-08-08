from django.shortcuts import render
from django.views import generic
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
import datetime

from .models import Book, Author, BookInstance, Genre
from .forms import RenewBookForm

@login_required
def index(request):
    """
    View function for home page of site.
    """
    # Generate counts of some of the main objects
    num_books = Book.objects.all().count()
    num_instances = BookInstance.objects.all().count()

    # Available books (status = 'a')
    num_instances_available = BookInstance.objects.filter(status__exact='a').count()
    num_authors = Author.objects.count() # The 'all()' is implied by default.
    num_genres = Genre.objects.count()
    num_books_pattern = Book.objects.filter(title__icontains='androids').count()

    num_visits = request.session.get('num_visits', 0)
    request.session['num_visits'] = num_visits + 1

    # Render the HTML template index.html with the data in the context variable
    return render(
        request,
        'index.html',
        context = {
            'num_books':num_books,
            'num_instances':num_instances,
            'num_instances_available':num_instances_available,
            'num_authors':num_authors,
            'num_genres':num_genres,
            'num_books_pattern':num_books_pattern,
            'num_visits': num_visits,
        },
    )

class BookListView(LoginRequiredMixin, generic.ListView):
    model = Book
    paginate_by = 5

class BookDetailView(generic.DetailView):
    model = Book

class AuthorListView(generic.ListView):
    model = Author
    paginate_by = 10

class AuthorDetailView(generic.DetailView):
    model = Author

class LoanedBooksByUserListView(LoginRequiredMixin, generic.ListView):
    """
    Generic class-based view listing books on loan to current user.
    """
    model = BookInstance
    template_name = 'catalog/bookinstance_list_borrowed_user.html'
    paginate_by = 10

    def get_queryset(self):
        return BookInstance.objects.filter(borrower=self.request.user).filter(status__exact='o').order_by('due_back')

class LoanedBooksListView(PermissionRequiredMixin, generic.ListView):
    """
    Generic class-based view listing all books on loan to anyone.
    """
    model = BookInstance
    template_name = 'catalog/bookinstance_list_borrowed.html'
    paginate_by = 10
    permission_required = 'catalog.can_mark_returned'

    def get_queryset(self):
        return BookInstance.objects.filter(status__exact='o').order_by('due_back')

@permission_required('catalog.can_mark_returned') # reuse can_mark_returned here. TODO: create a new permission
def renew_book_librarian(request, pk):
    book_inst = get_object_or_404(BookInstance, pk = pk)

    # If this is a POST request, then process the Form data
    if request.method == 'POST':

        # 1. BINDING
        # Create a form instance and populate it with data from the request
        form = RenewBookForm(request.POST)

        # 2. Check if the form is valid - runs all default validation + clean_xxx functions in the RenewBookForm class
        #  if the form is NOT valid, render will be called with 'form' containing the error message(s)
        if form.is_valid():
            # 3. Process the data in form.cleaned_data as required (here we just write it to the model due_back field)
            # Clean and sanitize data for potentially unsafe input
            # and convert into standard python type for data
            book_inst.due_back = form.cleaned_data['renewal_date']
            book_inst.save()

            # 4. Redirect to a new URL:
            return HttpResponseRedirect(reverse('borrowed'))

    # If this is a GET (or any other method) create the default form
    else:
        proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=3)
        form = RenewBookForm(initial={'renewal_date': proposed_renewal_date,})

    return render(request, 'catalog/book_renew_librarian.html', {'form': form, 'bookinst': book_inst})

class AuthorCreate(PermissionRequiredMixin, CreateView):
    model = Author
    fields = '__all__'
    initial = {'date_of_death': '12/10/2016',} # this is how you define initial values of fields
    permission_required = 'catalog.add_author'

class AuthorUpdate(PermissionRequiredMixin, UpdateView):
    model = Author
    fields = ['first_name', 'last_name', 'date_of_birth', 'date_of_death']
    permission_required = 'catalog.change_author'

class AuthorDelete(PermissionRequiredMixin, DeleteView):
    model = Author
    success_url = reverse_lazy('authors')
    permission_required = 'catalog.delete_author'

class BookCreate(PermissionRequiredMixin, CreateView):
    model = Book
    fields = '__all__'
    permission_required = 'catalog.add_book'

class BookUpdate(PermissionRequiredMixin, UpdateView):
    model = Book
    fields = '__all__'
    permission_required = 'catalog.change_book'

class BookDelete(PermissionRequiredMixin, DeleteView):
    model = Book
    success_url = reverse_lazy('books')
    permission_required = 'catalog.delete_book'