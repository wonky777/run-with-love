"""
Команда автоимпорта новостей из ВКонтакте (раздел 19.1 ТЗ).

Использование:
    python manage.py import_vk            # импортировать последние 10 постов
    python manage.py import_vk --count 5  # импортировать последние 5 постов
    python manage.py import_vk --no-images

Можно поставить на расписание (cron / планировщик), чтобы новости подтягивались
автоматически. Ручное создание новостей в админке при этом продолжает работать.
"""

from django.core.management.base import BaseCommand, CommandError

from content.services.vk_api import import_latest_from_vk, VKApiError, VK_KEEP_LAST


class Command(BaseCommand):
    help = "Импортирует последние новости из сообщества ВКонтакте через VK API."

    def add_arguments(self, parser):
        parser.add_argument(
            "--count", type=int, default=VK_KEEP_LAST,
            help=f"Сколько последних постов запросить (по умолчанию {VK_KEEP_LAST}).",
        )
        parser.add_argument(
            "--no-images", action="store_true",
            help="Не скачивать изображения постов.",
        )

    def handle(self, *args, **options):
        try:
            stats = import_latest_from_vk(
                count=options["count"],
                download_images=not options["no_images"],
            )
        except VKApiError as exc:
            raise CommandError(str(exc))

        self.stdout.write(self.style.SUCCESS(
            "Импорт из ВК завершён: "
            f"получено {stats['fetched']}, "
            f"создано {stats['created']}, "
            f"обновлено {stats['updated']}, "
            f"удалено старых {stats['pruned']}."
        ))
