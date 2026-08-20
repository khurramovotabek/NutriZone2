from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.brand.models import Brand, BrandTranslation
from apps.category.models import Category, CategoryTranslation
from apps.locations.models import City, Country, Region
from apps.products.models import Product, ProductSpecification, ProductTranslation, ProductVariant

User = get_user_model()


def _category(slug, parent, translations, **kwargs):
    category, _ = Category.objects.get_or_create(slug=slug, defaults={"parent": parent, **kwargs})
    for language, name in translations.items():
        CategoryTranslation.objects.get_or_create(
            category=category, language=language, defaults={"name": name}
        )
    return category


def _brand(name, translations, **kwargs):
    brand, _ = Brand.objects.get_or_create(name=name, defaults=kwargs)
    for language, description in translations.items():
        BrandTranslation.objects.get_or_create(
            brand=brand, language=language, defaults={"description": description}
        )
    return brand


def _product(slug, category, brand, translations):
    product, created = Product.objects.get_or_create(
        slug=slug, defaults={"category": category, "brand": brand}
    )
    for language, fields in translations.items():
        ProductTranslation.objects.get_or_create(product=product, language=language, defaults=fields)
    return product, created


class Command(BaseCommand):
    help = "Seeds the database with demo locations, categories, brands, and products for local development."

    @transaction.atomic
    def handle(self, *args, **options):
        if not User.objects.filter(is_superuser=True).exists():
            User.objects.create_superuser(
                username="admin", email="admin@nutrizone.local", password="admin12345"
            )
            self.stdout.write(self.style.SUCCESS("Created superuser 'admin' / 'admin12345'"))

        uzbekistan, _ = Country.objects.get_or_create(name="Uzbekistan", defaults={"code": "UZ"})
        usa, _ = Country.objects.get_or_create(name="United States", defaults={"code": "US"})

        tashkent_region, _ = Region.objects.get_or_create(country=uzbekistan, name="Tashkent Region")
        samarkand_region, _ = Region.objects.get_or_create(country=uzbekistan, name="Samarkand Region")
        City.objects.get_or_create(region=tashkent_region, name="Tashkent")
        City.objects.get_or_create(region=samarkand_region, name="Samarkand")

        # Nested category tree, seeded with real uz/ru/en translations so the
        # multilingual system has something real to show end to end.
        sports_nutrition = _category(
            "sports-nutrition",
            None,
            {"uz": "Sport ovqatlanishi", "ru": "Спортивное питание", "en": "Sports Nutrition"},
            sort_order=1,
            icon="dumbbell",
        )
        protein = _category(
            "protein",
            sports_nutrition,
            {"uz": "Oqsil", "ru": "Протеин", "en": "Protein"},
            sort_order=1,
            icon="beef",
        )
        whey_protein = _category(
            "whey-protein",
            protein,
            {"uz": "Zardob oqsili", "ru": "Сывороточный протеин", "en": "Whey Protein"},
            sort_order=1,
        )
        _category(
            "casein-protein",
            protein,
            {"uz": "Kazein oqsili", "ru": "Казеиновый протеин", "en": "Casein Protein"},
            sort_order=2,
        )
        creatine_group = _category(
            "creatine",
            sports_nutrition,
            {"uz": "Kreatin", "ru": "Креатин", "en": "Creatine"},
            sort_order=2,
            icon="zap",
        )
        creatine = _category(
            "monohydrate",
            creatine_group,
            {"uz": "Monogidrat", "ru": "Моногидрат", "en": "Monohydrate"},
            sort_order=1,
        )
        vitamins_root = _category(
            "vitamins",
            None,
            {"uz": "Vitaminlar", "ru": "Витамины", "en": "Vitamins"},
            sort_order=2,
            icon="pill",
        )
        _category(
            "multivitamins",
            vitamins_root,
            {"uz": "Multivitaminlar", "ru": "Мультивитамины", "en": "Multivitamins"},
            sort_order=1,
        )

        applied = _brand(
            "Applied Nutrition",
            {
                "uz": "AQShning ishonchli sport ovqatlanish brendi.",
                "ru": "Надёжный бренд спортивного питания из США.",
                "en": "Trusted sports nutrition brand from the USA.",
            },
            country=usa,
        )
        optimum = _brand(
            "Optimum Nutrition",
            {
                "uz": "Dunyoda sotuvlar bo'yicha birinchi oqsil brendi.",
                "ru": "Протеиновый бренд номер один в мире по продажам.",
                "en": "World's #1 selling protein brand.",
            },
            country=usa,
        )

        whey, created = _product(
            "gold-standard-whey",
            whey_protein,
            optimum,
            {
                "uz": {
                    "name": "Gold Standard Whey",
                    "short_description": "Premium zardob oqsili izolyati aralashmasi.",
                    "description": "Mushaklarni tiklash va o'sishi uchun sohada yetakchi zardob oqsili.",
                },
                "ru": {
                    "name": "Gold Standard Whey",
                    "short_description": "Премиальная смесь изолята сывороточного протеина.",
                    "description": "Ведущий в отрасли сывороточный протеин для восстановления и роста мышц.",
                },
                "en": {
                    "name": "Gold Standard Whey",
                    "short_description": "Premium whey protein isolate blend.",
                    "description": "Industry-leading whey protein for muscle recovery and growth.",
                },
            },
        )
        if created:
            ProductVariant.objects.create(
                product=whey,
                sku="ON-WHEY-CHOC-900",
                price=Decimal("49.99"),
                quantity=25,
                weight="900g",
                flavor="Chocolate",
                is_default=True,
            )
            ProductVariant.objects.create(
                product=whey,
                sku="ON-WHEY-VAN-900",
                price=Decimal("49.99"),
                quantity=18,
                weight="900g",
                flavor="Vanilla",
            )
            ProductSpecification.objects.bulk_create(
                [
                    ProductSpecification(product=whey, label="Protein", value="24g", sort_order=1),
                    ProductSpecification(product=whey, label="Calories", value="120 kcal", sort_order=2),
                    ProductSpecification(product=whey, label="Serving Size", value="30g", sort_order=3),
                ]
            )

        creatine_mono, created = _product(
            "creatine-monohydrate",
            creatine,
            applied,
            {
                "uz": {
                    "name": "Kreatin monogidrat",
                    "short_description": "Toza mikronizatsiyalangan kreatin monogidrat.",
                },
                "ru": {
                    "name": "Моногидрат креатина",
                    "short_description": "Чистый микронизированный моногидрат креатина.",
                },
                "en": {
                    "name": "Creatine Monohydrate",
                    "short_description": "Pure micronized creatine monohydrate.",
                },
            },
        )
        if created:
            ProductVariant.objects.create(
                product=creatine_mono,
                sku="AN-CREA-300",
                price=Decimal("19.99"),
                quantity=0,
                weight="300g",
                is_default=True,
                status=ProductVariant.Status.ACTIVE,
            )
            ProductVariant.objects.create(
                product=creatine_mono,
                sku="AN-CREA-500",
                price=Decimal("29.99"),
                quantity=40,
                weight="500g",
            )
            ProductSpecification.objects.create(
                product=creatine_mono, label="Creatine Monohydrate", value="5g", sort_order=1
            )

        self.stdout.write(
            self.style.SUCCESS("Demo data seeded successfully (uz/ru/en translations included).")
        )
