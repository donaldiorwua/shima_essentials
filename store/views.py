from django.shortcuts import get_object_or_404, render

from .models import Category, Product


def product_list(request):
    products = Product.objects.filter(available=True).order_by("name")

    return render(
        request,
        "store/product_list.html",
        {"products": products},
    )


def category_products(request, slug):
    category = get_object_or_404(
        Category,
        slug=slug,
        active=True,
    )

    products = Product.objects.filter(
        category=category,
        available=True,
    ).order_by("name")

    return render(
        request,
        "store/product_list.html",
        {
            "products": products,
            "category": category,
        },
    )

def product_detail(request, product_id):
    product = get_object_or_404(
        Product,
        id=product_id,
        available=True,
    )

    return render(
        request,
        "store/product_detail.html",
        {"product": product},
    )

def home(request):
    products = Product.objects.filter(available=True).order_by("name")
    categories = Category.objects.filter(active=True).order_by("name")

    return render(
        request,
        "store/home.html",
        {
            "products": products,
            "categories": categories,
        },
    )
