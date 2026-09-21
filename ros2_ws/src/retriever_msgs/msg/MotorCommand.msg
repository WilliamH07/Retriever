# Consigne de banc pour le nœud MOTION : un rapport cyclique signé par moteur.
#
#   -1.0 = pleine vitesse arrière, +1.0 = pleine vitesse avant, 0 = arrêt.
#
# ⚠️ Ce n'est PAS une vitesse. Le variateur ZS-X11H reçoit une tension VR et
# fait ce qu'il veut avec ; la vitesse réelle dépend de la charge et de la
# batterie. La consigne en rad/s viendra avec le retour Hall et ros2_control.
#
# Le pont républie la dernière consigne à 50 Hz vers l'ESP32, et l'annule si
# ce message ne se renouvelle pas pendant `motors.command_timeout_s` : lâcher
# le panneau Foxglove arrête les roues.
#
# Dimensionné pour quatre moteurs. Les moteurs non câblés ignorent leur case.
std_msgs/Header header
float32[4] duty
