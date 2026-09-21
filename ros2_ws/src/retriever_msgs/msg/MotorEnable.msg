# Autorisation par moteur. Un bit par moteur, b0 = moteur 0.
#
# Au démarrage du nœud MOTION, rien n'est autorisé : aucune consigne ne sort
# avant ce message. Envoyer 0 coupe tout. Après un ESTOP logiciel, il faut
# renvoyer un masque non nul pour ré-armer.
uint8 enable_mask
