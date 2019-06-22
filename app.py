from flask import Flask
from flask_graphql import GraphQLView
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from flask_sqlalchemy import SQLAlchemy
import graphene
from graphene import relay
from graphene_sqlalchemy import SQLAlchemyConnectionField, SQLAlchemyObjectType

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']

db = SQLAlchemy(app)

class User(db.Model):
	__tablename__ = 'users'
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.Text)
	email = db.Column(db.Text)
	username = db.Column(db.Text)

db.create_all()


class Users(SQLAlchemyObjectType):
	class Meta:
	    model = User
	    interfaces = (relay.Node, )

class createUser(graphene.Mutation):
	class Input:
		name = graphene.String()
		email = graphene.String()
		username = graphene.String()
	ok = graphene.Boolean()
	user = graphene.Field(Users)

	@classmethod
	def mutate(cls, _, args, context, info):
		user = UserModel(name=args.get('name'), email=args.get('email'), username=args.get('username'))
		db_session.add(user)
		db_session.commit()
		ok = True
		return createUser(user=user, ok=ok)

class changeUsername(graphene.Mutation):
	class Input:
		username = graphene.String()
		email = graphene.String()

	ok = graphene.Boolean()
	user = graphene.Field(Users)

	@classmethod
	def mutate(cls, _, args, context, info):
		query = Users.get_query(context)
		email = args.get('email')
		username = args.get('username')
		user = query.filter(UserModel.email == email).first()
		user.username = username
		db_session.commit()
		ok = True

		return changeUsername(user=user, ok = ok)

class Query(graphene.ObjectType):
	node = relay.Node.Field()
	user = SQLAlchemyConnectionField(Users)
	find_user = graphene.Field(lambda: Users, username = graphene.String())
	all_users = SQLAlchemyConnectionField(Users)

	def resolve_find_user(self,args,context,info):
		query = Users.get_query(context)
		username = args.get('username')
		return query.filter(UserModel.username == username).first()

class MyMutations(graphene.ObjectType):
	create_user = createUser.Field()
	change_username = changeUsername.Field()


schema = graphene.Schema(query=Query, mutation=MyMutations, types=[Users])

engine = create_engine(os.environ['DATABASE_URL'], convert_unicode=True)
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))

app.add_url_rule('/graphql', view_func=GraphQLView.as_view('graphql', schema=schema, graphiql=True, context={'session': db_session}))

@app.route('/')
def index():
	return "For the demo, navigate to the endpoint /graphql"

if __name__ == "__main__":
	app.run(debug=True, use_reloader=True)
