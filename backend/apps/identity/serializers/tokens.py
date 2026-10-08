from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class SharedTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = "identifier"

    def validate(self, attrs):
        identifier = attrs.get(self.username_field, "")
        if isinstance(identifier, str):
            attrs[self.username_field] = identifier.strip()
        return super().validate(attrs)
