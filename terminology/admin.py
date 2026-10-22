from django.contrib import admin

from .models import RefBook, RefBookElement, RefBookVersion
from .services import get_current_version




class RefBookElementInline(admin.TabularInline):
	model = RefBookElement
	extra = 0
	fields = ('code', 'value')


class RefBookVersionInline(admin.TabularInline):
	model = RefBookVersion
	extra = 0
	fields = ('version', 'start_date')


@admin.register(RefBook)
class RefBookAdmin(admin.ModelAdmin):
	list_display = ('id', 'code', 'name', 'current_version', 'current_start_date')
	search_fields = ('code', 'name')
	inlines = (RefBookVersionInline,)

	@admin.display(description='Текущая версия')
	def current_version(self, obj):
		version = get_current_version(obj)
		return version.version if version else '—'

	@admin.display(description='Дата начала текущей версии')
	def current_start_date(self, obj):
		version = get_current_version(obj)
		return version.start_date if version else '—'


@admin.register(RefBookVersion)
class RefBookVersionAdmin(admin.ModelAdmin):
	list_display = ('refbook_code', 'refbook_name', 'version', 'start_date')
	list_filter = ('refbook',)
	search_fields = ('refbook__code', 'refbook__name', 'version')
	autocomplete_fields = ('refbook',)
	inlines = (RefBookElementInline,)

	@admin.display(description='Код справочника', ordering='refbook__code')
	def refbook_code(self, obj):
		return obj.refbook.code

	@admin.display(description='Наименование справочника', ordering='refbook__name')
	def refbook_name(self, obj):
		return obj.refbook.name


@admin.register(RefBookElement)
class RefBookElementAdmin(admin.ModelAdmin):
	list_display = ('code', 'value', 'refbook_code', 'version_label')
	list_filter = ('refbook_version__refbook', 'refbook_version')
	search_fields = ('code', 'value', 'refbook_version__refbook__code')
	autocomplete_fields = ('refbook_version',)

	@admin.display(description='Справочник', ordering='refbook_version__refbook__code')
	def refbook_code(self, obj):
		return obj.refbook_version.refbook.code

	@admin.display(description='Версия', ordering='refbook_version__version')
	def version_label(self, obj):
		return obj.refbook_version.version



admin.site.site_header = 'Администрирование сервиса терминологии'
admin.site.site_title = 'Сервис терминологии'
admin.site.index_title = 'Управление справочниками'
