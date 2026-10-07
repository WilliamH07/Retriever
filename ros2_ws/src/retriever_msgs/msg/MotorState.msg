# Ce que le nœud MOTION applique réellement, à comparer avec la commande.
std_msgs/Header header

uint8 FLAG_ENABLED     = 1     # au moins un moteur autorisé
uint8 FLAG_CMD_TIMEOUT = 2     # le nœud n'a rien reçu depuis > 500 ms : consignes à zéro
uint8 FLAG_ESTOP       = 4     # arrêt logiciel, ré-armer par MotorEnable
uint8 FLAG_OUTPUT_FAULT = 16
uint8 FLAG_PROTOCOL_BLOCKED = 32
uint8 FLAG_REVERSING = 64
uint8 FLAG_LIMITED = 128

uint8 node_id          # 2 avant/banc quatre roues ; 3 arriere

uint8 FLAG_NEVER_ARMED = 8     # aucun MotorEnable depuis le démarrage du nœud

float32[4] applied     # consigne en sortie, après chien de garde, masque et pente
uint8 enable_mask
uint8 flags
uint16 cmd_age_ms      # âge de la dernière MOTOR_CMD vue par le nœud
