import face_recognition  # biometric identification component
def identify(image):
    return face_recognition.face_encodings(image)
