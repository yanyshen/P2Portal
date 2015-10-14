from django.contrib.auth.backends import RemoteUserBackend
from django.contrib.auth.models import User

class ASOUserBackend(RemoteUserBackend):
	
	def get_user(self, user_id):
		try:
			return User.objects.get(pk=user_id)
		except User.DoesNotExist:
			return None
	
# 	def has_perm(self,user_obj, perm, obj=None):
# 		if user_obj.is_active:
# 			return True
# 		else:
# 			return False
		
		
	
		