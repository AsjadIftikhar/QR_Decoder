from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from upload_process.controller import execute_script
from django.contrib import messages


# Imaginary function to handle an uploaded file.
# from somewhere import handle_uploaded_file

def homePage(request):
    if request.method == 'POST':
        uploaded_file = request.FILES.getlist('sentFile')
        output_name = request.POST.get('GSheet')
        fs = FileSystemStorage()
        if uploaded_file:
            for f in uploaded_file:
                fs.save(f.name, f)

            result = execute_script(output_name)
            if result:
                messages.error(request, "Sheet Not Found")

    context = {}
    return render(request, 'home.html', context)
