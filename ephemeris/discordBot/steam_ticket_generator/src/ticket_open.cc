#include <iostream>
#include <string>
#include <cstdint>
#include <thread>
#include <chrono>
#include <steam/steam_api.h>

std::string ticketToHex(const uint8_t* buffer, uint32_t size) {
    std::string hex;
    hex.reserve(size * 2);
    for (uint32_t i = 0; i < size; i++) {
        char buf[3];
        snprintf(buf, sizeof(buf), "%02x", buffer[i]);
        hex += buf;
    }
    return hex;
}

int main() {
    if (!SteamAPI_Init()) {
        std::cerr << "Failed to initialize Steam API. Make sure Steam is running." << std::endl;
        return 1;
    }

    if (!SteamUser()->BLoggedOn()) {
        std::cerr << "User is not logged into Steam." << std::endl;
        SteamAPI_Shutdown();
        return 1;
    }

    uint8_t ticketBuffer[1024];
    uint32_t ticketSize = 0;

    SteamNetworkingIdentity identity;
    identity.SetSteamID(SteamUser()->GetSteamID());

    HAuthTicket ticketHandle = SteamUser()->GetAuthSessionTicket(
        ticketBuffer,
        sizeof(ticketBuffer),
        &ticketSize,
        &identity
    );

    if (ticketHandle == k_HAuthTicketInvalid) {
        std::cerr << "Failed to get auth session ticket." << std::endl;
        SteamAPI_Shutdown();
        return 1;
    }

    // Wait for ticket to be ready via callbacks
    for (int i = 0; i < 10; i++) {
        SteamAPI_RunCallbacks();
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
    }

    std::string ticketHex = ticketToHex(ticketBuffer, ticketSize);
    std::cout << ticketHex << std::endl;

    SteamAPI_Shutdown();
    return 0;
}
