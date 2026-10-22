from django.db import models


class RefBook(models.Model):
    code = models.CharField('Код', max_length=100, unique=True)
    name = models.CharField('Наименование', max_length=300)
    description = models.TextField('Описание', blank=True)

    class Meta:
        verbose_name = 'справочник'
        verbose_name_plural = 'справочники'
        ordering = ('code',)

    def __str__(self):
        return f'{self.code} — {self.name}'


class RefBookVersion(models.Model):
    refbook = models.ForeignKey(
        RefBook,
        on_delete=models.CASCADE,
        related_name='versions',
        verbose_name='Справочник',
    )
    version = models.CharField('Версия', max_length=50)
    start_date = models.DateField('Дата начала действия')

    class Meta:
        verbose_name = 'версия справочника'
        verbose_name_plural = 'версии справочников'
        ordering = ('refbook__code', '-start_date', 'version')
        constraints = [
            models.UniqueConstraint(
                fields=('refbook', 'version'), name='uniq_refbook_version'
            ),
            models.UniqueConstraint(
                fields=('refbook', 'start_date'), name='uniq_refbook_start_date'
            ),
        ]
        indexes = [models.Index(fields=('refbook', 'start_date'))]

    def __str__(self):
        return f'{self.refbook.code} / {self.version} ({self.start_date})'


class RefBookElement(models.Model):
    refbook_version = models.ForeignKey(
        RefBookVersion,
        on_delete=models.CASCADE,
        related_name='elements',
        verbose_name='Версия справочника',
    )
    code = models.CharField('Код элемента', max_length=100)
    value = models.CharField('Значение', max_length=300)

    class Meta:
        verbose_name = 'элемент справочника'
        verbose_name_plural = 'элементы справочника'
        ordering = ('code',)
        constraints = [
            models.UniqueConstraint(
                fields=('refbook_version', 'code'), name='uniq_version_element_code'
            ),
        ]
        indexes = [models.Index(fields=('refbook_version', 'code'))]

    def __str__(self):
        return f'{self.code} — {self.value}'
