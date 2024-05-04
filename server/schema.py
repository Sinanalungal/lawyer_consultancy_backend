import graphene

class Query(graphene.ObjectType):
    hello = graphene.String(default_value="Hi!")
    check =graphene.String(default_value="it's working !!!!")

schema = graphene.Schema(query=Query)