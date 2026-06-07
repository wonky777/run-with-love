"""
Наполняет базу демо-данными для проверки (необязательная команда).

    python manage.py seed_demo

Создаёт по нескольку забегов, новостей, партнёров, благополучателей и альбомов,
включая записи с is_visible=False для проверки фильтрации API.
"""

from datetime import date

from django.core.management.base import BaseCommand

from content.models import (
    Beneficiary,
    Gallery,
    News,
    Partner,
    Race,
    RaceDistance,
)


class Command(BaseCommand):
    help = "Создаёт демонстрационные данные."

    def handle(self, *args, **options):
        p1 = Partner.objects.create(
            name="Партнёр «Беги добро»", description="Спортивный партнёр.",
            website_url="https://example.com", sort_order=1,
        )
        Partner.objects.create(
            name="Скрытый партнёр", description="Не должен попасть в API.",
            is_visible=False,
        )

        b1 = Beneficiary.objects.create(
            name="Фонд «Надежда для детей»",
            description="Поддержка детских программ.",
            website_url="https://example.org", sort_order=1,
        )

        race = Race.objects.create(
            title="Весенний городской забег",
            date=date(2026, 5, 15),
            status=Race.STATUS_REGISTRATION_OPEN,
            short_description="Краткое описание весеннего забега.",
            description="Полное описание весеннего забега.",
            location_text="Москва, Парк Горького",
            russian_running_url="https://russiarunning.com/example",
            sort_order=1,
        )
        race.partners.add(p1)
        race.beneficiaries.add(b1)
        RaceDistance.objects.create(race=race, length="5 км", age_category="18+", sort_order=1)
        RaceDistance.objects.create(race=race, length="1 км", age_category="детский забег", sort_order=2)

        Race.objects.create(
            title="Скрытый забег", date=date(2026, 7, 1),
            status=Race.STATUS_UPCOMING, is_visible=False,
        )

        News.objects.create(
            title="Весенний забег собрал средства на здравоохранение",
            text="Подробности о результатах забега.",
            date=date(2026, 3, 28), sort_order=1,
        )
        News.objects.create(
            title="Скрытая новость", text="Не в API.",
            date=date(2026, 3, 1), is_visible=False,
        )

        Gallery.objects.create(
            title="Фотоотчёт с весеннего забега",
            description="Лучшие моменты.",
            race=race, date=date(2026, 5, 15), sort_order=1,
        )

        self.stdout.write(self.style.SUCCESS("Демо-данные созданы."))
