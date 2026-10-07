# Tests hôte du firmware.
#
#     make            compile et exécute
#     make clean
#
# Ces tests ne demandent ni ESP-IDF, ni matériel, ni ROS : un compilateur C
# suffit. C'est délibéré — un test qu'on ne peut lancer qu'avec le robot sur
# l'établi n'est pas lancé.

CC      ?= gcc
CFLAGS  ?= -std=c99 -Wall -Wextra -Werror -O2
INCLUDES = -I../esp32_motion/main -I../protocol/generated -I../components/retriever_link/portable
PORTABLE = ../components/retriever_link/portable
BUILD    = build

SRCS_FRAMING = $(PORTABLE)/rt_cobs.c $(PORTABLE)/rt_crc16.c $(PORTABLE)/rt_framing.c

.PHONY: all run clean vectors

all: run

$(BUILD):
	@mkdir -p $(BUILD)

$(BUILD)/test_protocol: test_protocol.c | $(BUILD)
	$(CC) $(CFLAGS) $(INCLUDES) $< -lm -o $@

$(BUILD)/test_framing: test_framing.c $(SRCS_FRAMING) | $(BUILD)
	$(CC) $(CFLAGS) $(INCLUDES) $^ -o $@

# ⚠️ L'en-tête généré est une dépendance EXPLICITE. Sans elle, un changement de
# protocole ne reconstruit pas ce binaire, la comparaison C ↔ Python se fait
# contre l'ANCIEN protocole et signale des dizaines d'échecs qui n'en sont pas —
# ou, pire, passe alors que les deux côtés ont divergé. Constaté le 20 septembre
# 2026 en ajoutant les trames moteur.
PROTO_HDR := ../protocol/generated/retriever_protocol.h

$(BUILD)/emit_vectors: emit_vectors.c $(SRCS_FRAMING) $(PROTO_HDR) | $(BUILD)
	$(CC) $(CFLAGS) $(INCLUDES) emit_vectors.c $(SRCS_FRAMING) -o $@

$(BUILD)/test_protocol: $(PROTO_HDR)

vectors: $(BUILD)/emit_vectors
	@$(BUILD)/emit_vectors

$(BUILD)/test_motor_control: test_motor_control.c ../esp32_motion/main/motor_control.c ../esp32_motion/main/motor_control.h $(PROTO_HDR) | $(BUILD)
	$(CC) $(CFLAGS) $(INCLUDES) test_motor_control.c ../esp32_motion/main/motor_control.c -lm -o $@

$(BUILD)/test_motor_outputs: test_motor_outputs.c $(wildcard fakes/*.h fakes/driver/*.h fakes/freertos/*.h) ../esp32_motion/main/motors.c ../esp32_motion/main/motors.h ../esp32_motion/main/motor_control.c ../esp32_motion/main/motor_control.h $(PROTO_HDR) | $(BUILD)
	$(CC) $(CFLAGS) -Ifakes $(INCLUDES) test_motor_outputs.c ../esp32_motion/main/motor_control.c -lm -o $@

run: $(BUILD)/test_protocol $(BUILD)/test_framing $(BUILD)/test_motor_control $(BUILD)/test_motor_outputs
	@echo "=== protocole ==="   && $(BUILD)/test_protocol
	@echo "=== cadrage ==="     && $(BUILD)/test_framing
	@$(BUILD)/test_motor_control
	@$(BUILD)/test_motor_outputs

clean:
	rm -rf $(BUILD)
