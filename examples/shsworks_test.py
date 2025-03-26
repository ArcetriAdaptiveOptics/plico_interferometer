import time
import plico_interferometer
import configparser

# Load configuration from the config file
config = configparser.ConfigParser()
config.read(r"C:\Users\labot\git\plico_interferometer_server\plico_interferometer_server\conf\plico_interferometer_server.conf")

# Extract hostServer and portServer from the configuration
hostServer = config['interferometer1']['host']
portServer = int(config['interferometer1']['port'])

def test_shs_connectivity_and_wavefront():
    try:
        # Create an instance of the OptocraftSHS class
        shs_device = plico_interferometer.interferometer(hostServer, portServer)

        # Check connectivity
        print("Testing connectivity...")
        print(f"Device status: {shs_device.status()}")
        
        # Grab a wavefront
        print("Grabbing wavefront...")
        wavefront_data = shs_device.wavefront(1, timeout_in_sec=20)
        
        # Output the wavefront data
        print("Wavefront data retrieved successfully:")
        print(wavefront_data)

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    test_shs_connectivity_and_wavefront()