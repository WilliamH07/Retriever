# Projet ESP-IDF — nœud MOTION de Retriever, version BANC.
#
#   idf.py set-target esp32
#   idf.py build flash
#
# Une DevKitC dédiée, distincte du nœud SAFETY/IMU : c'est l'architecture du
# dossier (§F), et c'est ce qui fait qu'un bug moteur n'emporte pas l'IMU. Les
# deux nœuds partagent les composants de firmware/components/ — un seul
# protocole, un seul cadrage, un seul hash.

cmake_minimum_required(VERSION 3.16)

set(EXTRA_COMPONENT_DIRS "${CMAKE_CURRENT_LIST_DIR}/../components")

include($ENV{IDF_PATH}/tools/cmake/project.cmake)
project(retriever_motion)
