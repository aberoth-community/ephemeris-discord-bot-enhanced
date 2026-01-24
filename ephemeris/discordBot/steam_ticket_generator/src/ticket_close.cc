#include <iostream>
#include <string>
#include <steam/steam_api.h>

int main(int argc, const char** argv) {
    if (argc < 2) {
        std::cout << "Usage: ticket_close <ticket>\n";
        return 1;
    }
    if (!SteamAPI_Init()) {
        std::cerr << "Failed to initialize Steam API. Make sure Steam is running." << std::endl;
        return 1;
    }
    if (!SteamUser()->BLoggedOn()) {
        std::cerr << "User is not logged into Steam." << std::endl;
        SteamAPI_Shutdown();
        return 1;
    }

    HAuthTicket ticket = static_cast<HAuthTicket>(std::stoul(argv[1]));
    SteamUser()->CancelAuthTicket(ticket);
    SteamAPI_Shutdown();

    std::cout << "OK\n";
    return 0;
} 
