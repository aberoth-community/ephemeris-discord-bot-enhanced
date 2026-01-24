cmake_minimum_required(VERSION 3.16)
project(GoldenTicket)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_executable(ticket_close src/ticket_close.cc)
target_include_directories(ticket_close PRIVATE ${CMAKE_SOURCE_DIR}/sdk/public)
target_link_directories(ticket_close PRIVATE ${CMAKE_SOURCE_DIR}/sdk/redistributable_bin/win64)
target_link_libraries(ticket_close steam_api64)

add_executable(ticket_open src/ticket_open.cc)
target_include_directories(ticket_open PRIVATE ${CMAKE_SOURCE_DIR}/sdk/public)
target_link_directories(ticket_open PRIVATE ${CMAKE_SOURCE_DIR}/sdk/redistributable_bin/win64)
target_link_libraries(ticket_open steam_api64)

add_custom_command(TARGET ticket_open POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_if_different
    ${CMAKE_SOURCE_DIR}/sdk/redistributable_bin/win64/steam_api64.dll
    $<TARGET_FILE_DIR:ticket_open>)
