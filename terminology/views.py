from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
)

from .models import RefBook, RefBookVersion
from .serializers import (
    CheckElementQuerySerializer,
    ElementCheckResponseSerializer,
    ElementsResponseSerializer,
    RefBookListResponseSerializer,
    RefBookQuerySerializer,
    VersionQuerySerializer,
)
from .services import get_current_version


class RefBookListView(APIView):
    @extend_schema(
        summary='Получить справочники',
        description=(
            'Без date возвращает все справочники. С date возвращает справочники, '
            'имеющие хотя бы одну версию с датой начала не позже указанной.'
        ),
        parameters=[
            OpenApiParameter(
                'date',
                OpenApiTypes.DATE,
                description='Дата в формате ГГГГ-ММ-ДД',
                required=False,
                examples=[OpenApiExample('На дату', value='2026-10-21')],
            )
        ],
        responses={200: RefBookListResponseSerializer, 400: OpenApiResponse(description='Некорректная дата')},
        examples=[
            OpenApiExample(
                'Список справочников',
                value={'refbooks': [{'id': 1, 'code': 'MS1', 'name': 'Медицинские специальности'}]},
                response_only=True,
            )
        ],
    )
    def get(self, request):
        query = RefBookQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        refbooks = RefBook.objects.all()
        print('query.validated_data', query.validated_data)
        if 'date' in query.validated_data:
            refbooks = refbooks.filter(
                versions__start_date__lte=query.validated_data['date']
            ).distinct()
        print(RefBookListResponseSerializer({'refbooks': refbooks}).data)
        return Response(RefBookListResponseSerializer({'refbooks': refbooks}).data)


class RefBookElementsView(APIView):
    @extend_schema(
        summary='Получить элементы версии',
        description=(
            'При version возвращает элементы указанной версии этого справочника. '
            'Иначе выбирает версию с самой поздней start_date, не превышающей текущую дату. '
            'Если подходящей версии нет, возвращает 404. Существующая версия без элементов '
            'возвращает пустой список.'
        ),
        parameters=[
            OpenApiParameter('refbook_id', int, location=OpenApiParameter.PATH),
            OpenApiParameter(
                'version',
                OpenApiTypes.STR,
                required=False,
                examples=[OpenApiExample('Версия', value='1.0')],
            ),
        ],
        responses={200: ElementsResponseSerializer, 404: OpenApiResponse(description='Справочник или версия не найдены')},
        examples=[
            OpenApiExample(
                'Элементы версии',
                value={'elements': [{'code': 'J00', 'value': 'Острый назофарингит'}]},
                response_only=True,
            )
        ],
    )
    def get(self, request, refbook_id):
        refbook = get_object_or_404(RefBook, pk=refbook_id)
        query = VersionQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        if 'version' in query.validated_data:
            version = RefBookVersion.objects.filter(
                refbook=refbook, version=query.validated_data['version']
            ).first()
        else:
            version = get_current_version(refbook)
        if version is None:
            raise NotFound('Версия справочника не найдена.')
        return Response(ElementsResponseSerializer({'elements': version.elements.all()}).data)


class CheckElementView(APIView):
    @extend_schema(
        summary='Проверить элемент справочника',
        description=(
            'Проверяет одновременное совпадение code и value внутри выбранной версии '
            'справочника. Без version применяется текущая версия. Несовпадение является '
            'результатом проверки is_valid=false (HTTP 200), а отсутствующий справочник '
            'или версия являются 404.'
        ),
        parameters=[
            OpenApiParameter('refbook_id', int, location=OpenApiParameter.PATH),
            OpenApiParameter(
                'code',
                OpenApiTypes.STR,
                required=True,
                examples=[OpenApiExample('Код элемента', value='J00')],
            ),
            OpenApiParameter(
                'value',
                OpenApiTypes.STR,
                required=True,
                examples=[OpenApiExample('Значение элемента', value='Острый назофарингит')],
            ),
            OpenApiParameter(
                'version',
                OpenApiTypes.STR,
                required=False,
                examples=[OpenApiExample('Версия', value='1.0')],
            ),
        ],
        responses={
            200: ElementCheckResponseSerializer,
            400: OpenApiResponse(description='Отсутствует или некорректен параметр'),
            404: OpenApiResponse(description='Справочник или версия не найдены'),
        },
        examples=[
            OpenApiExample(
                'Проверка пройдена', value={'is_valid': True}, response_only=True
            ),
            OpenApiExample(
                'Проверка не пройдена', value={'is_valid': False}, response_only=True
            ),
        ],
    )
    def get(self, request, refbook_id):
        refbook = get_object_or_404(RefBook, pk=refbook_id)
        query = CheckElementQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        if 'version' in query.validated_data:
            version = RefBookVersion.objects.filter(
                refbook=refbook, version=query.validated_data['version']
            ).first()
        else:
            version = get_current_version(refbook)
        if version is None:
            raise NotFound('Версия справочника не найдена.')
        is_valid = version.elements.filter(
            code=query.validated_data['code'], value=query.validated_data['value']
        ).exists()
        return Response({'is_valid': is_valid})
