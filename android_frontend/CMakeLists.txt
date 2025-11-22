cmake_minimum_required(VERSION 3.16)
project(TricorderFrontend LANGUAGES CXX)

set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)
set(CMAKE_AUTOUIC ON)

# Prefer finding core Qt modules first; check Mqtt separately to provide
# a clearer error message if the Qt MQTT add-on is not installed.
find_package(Qt6 REQUIRED COMPONENTS Core Quick Qml Gui)
find_package(Qt6 COMPONENTS Mqtt)
if(NOT Qt6_FOUND)
    message(FATAL_ERROR "Could not find Qt6. Make sure Qt is installed and CMAKE_PREFIX_PATH points to your Qt installation.")
endif()
if(NOT TARGET Qt6::Mqtt)
    message(FATAL_ERROR "Qt MQTT module not found.\n\nInstall the Qt MQTT add-on for your Qt version (use the Qt MaintenanceTool → Add or remove components),\nor install the Qt MQTT package that matches your Qt installation.\nAlternatively, run CMake with -DCMAKE_PREFIX_PATH=\"<path-to-Qt-lib-cmake>\" so find_package can locate Qt.\n\nExample: cmake .. -G \"Ninja\" -DCMAKE_PREFIX_PATH=\"C:/Qt/6.10.0/mingw_64/lib/cmake\"")
endif()

add_executable(${PROJECT_NAME}
    src/main.cpp
    src/tricorderbackend.cpp
    src/tricorderbackend.h
    qml.qrc
)

target_include_directories(${PROJECT_NAME} PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/src)

target_link_libraries(${PROJECT_NAME}
    Qt6::Core
    Qt6::Gui
    Qt6::Qml
    Qt6::Quick
    Qt6::Mqtt
)

set_target_properties(${PROJECT_NAME} PROPERTIES
    CXX_STANDARD 17
    RUNTIME_OUTPUT_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/bin
)

# If building for Android, point CPack / packaging to our android folder so
# the custom AndroidManifest.xml and other resources are used when creating
# the APK. Qt's CMake packaging honors ANDROID_PACKAGE_SOURCE_DIR.
if(ANDROID)
    set(ANDROID_PACKAGE_SOURCE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/android")
endif()
