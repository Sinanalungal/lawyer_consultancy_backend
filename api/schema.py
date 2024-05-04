import graphene
from graphene_django import DjangoObjectType
from .models import CustomUser


class UserType(DjangoObjectType):
    class Meta:
        model=CustomUser
        fields=['full_name', 'email', 'phone_number', 'password', 'role','is_verified']


class Query(graphene.ObjectType):
    all_users = graphene.List(UserType,id=graphene.Int())

    def resolve_all_users(self, info , id=None):
        if id is not None:
            return CustomUser.objects.filter(id=id)
        return CustomUser.objects.all()


schema = graphene.Schema(query=Query)