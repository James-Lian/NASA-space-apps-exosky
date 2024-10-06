from OpenGL.GL import * 
from OpenGL.GLU import * 
import pygame
import math
from astroquery.gaia import Gaia

# Define colors
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)  # Color for the star name display

# Function to convert RA, Dec, and distance into Cartesian coordinates
def convert_to_cartesian(ra, dec, dist):
    # Convert RA and Dec to radians from degrees
    ra = math.radians(ra)  # Convert RA (Right Ascension) to radians
    dec = math.radians(dec)  # Convert Dec (Declination) to radians

    # Convert distance to Cartesian coordinates
    x = dist * math.cos(ra) * math.cos(dec)
    y = dist * math.sin(ra) * math.cos(dec)
    z = dist * math.sin(dec)
    return (x, y, z)

def calculate_distance(ra1, dec1, ra2, dec2):
    # Simple Euclidean distance for demonstration; we might need a more accurate celestial distance calculation
    return ((ra1 - ra2) ** 2 + (dec1 - dec2) ** 2) ** 0.5

# Fetch star data from Gaia Catalog
def fetch_star_data(exo_ra, exo_dec):
    stars = []
    
    # Query to fetch data
    query = f"""
    SELECT SOURCE_ID, ra, dec, parallax
    FROM gaiadr3.gaia_source
    WHERE DISTANCE(POINT({exo_ra}, {exo_dec}), POINT(ra, dec)) < 1000000000000
    AND parallax IS NOT NULL
    """
    
    # Execute the query and get results
    job = Gaia.launch_job(query)
    result = job.get_results()
    parallaxes = []

    
    # Debug print the available columns
    #print("Available columns in the results:", result.colnames)

    for row in result:
        # Convert star coordinates to Cartesian and filter based on distance from (ra, dec)
        star_ra = row['ra']
        star_dec = row['dec']
        distance = calculate_distance(exo_ra, exo_dec, star_ra, star_dec)  # Implement calculate_distance method

        if distance < 1000:  # Define a threshold distance for "closeness"
            parallax = row['parallax']
            parallaxes.append(parallax)
            x, y, z = convert_to_cartesian(star_ra, star_dec, parallax)
            stars.append((row['SOURCE_ID'], star_ra, star_dec, distance, x, y, z))
    if parallaxes:
        print(f"Parallax range: min={min(parallaxes)}, max={max(parallaxes)}")
    return stars

    

# Draw the stars and Earth
def draw_stars(screen, stars, screen_width, screen_height, offset_x, offset_y, zoom_factor):
    pygame.draw.circle(screen, WHITE, (offset_x - offset_x + (screen_width/2), offset_y - offset_y + (screen_height/2)), 25) 
    
    for source_id, ra, dec, distance, x, y, z in stars:
        star_surface = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)

        # Project 3D coordinates to 2D
        x_2d, y_2d = project_3d_to_2d(x, y, z, screen_width, screen_height, offset_x, offset_y, zoom_factor)
        
        rings = 4 # number of gradient rings

        # Draw glow effect on star_surface
        for i in range(3, 0, -1):  # Larger to smaller for gradient effect
            glow_color = (255, 255, 0, int(255 * ((rings+1-i) / 6)))  # Yellow with gradient alpha
            pygame.draw.circle(star_surface, glow_color, 
                               (x_2d - offset_x + (screen_width // 2), y_2d - offset_y + (screen_height // 2)), 
                               3 * i + abs(int(z * 0.5)))
        
        # Draw the central star circle on top of the glow
        pygame.draw.circle(star_surface, YELLOW, 
                           (x_2d - offset_x + (screen_width // 2), y_2d - offset_y + (screen_height // 2)), 
                           3 + abs(int(0.5 * z)))

        # Blit the star surface onto the main screen
        screen.blit(star_surface, (0, 0))

# Project 3D point into 2D space with offset and zoom
def project_3d_to_2d(x, y, z, screen_width, screen_height, offset_x, offset_y, zoom_factor):
    factor = zoom_factor / (4 + z)  # Adjust for viewer distance
    x_2d = int(screen_width / 2 + (x + offset_x) * factor)
    y_2d = int(screen_height / 2 - (y + offset_y) * factor)
    return x_2d, y_2d

# Main function to open the pygame window
def open_pygame_window(ra, dec):
    pygame.init()

    x_exoplanet, y_exoplanet, z_exoplanet = convert_to_cartesian(ra, dec, 1)
    
    # Set up initial window size and display mode
    window_size = (800, 600)
    screen = pygame.display.set_mode(window_size, pygame.RESIZABLE)
    pygame.display.set_caption('Star Data Visualization')

    # Load font
    font = pygame.font.Font(None, 36)

    # Fetch star data
    stars = fetch_star_data(ra, dec)

    # Variables to track fullscreen toggle, panning and zoom
    is_fullscreen = False
    offset_x, offset_y = x_exoplanet, y_exoplanet
    zoom_factor = 300
    selected_star_name = None

    # Main loop for the Pygame window
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # Handle mouse clicks
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    mouse_x, mouse_y = event.pos
                    
                    # Check if any star is clicked
                    for source_id, ra, dec, distance, x, y, z in stars:
                        x_2d, y_2d = project_3d_to_2d(x, y, z, window_size[0], window_size[1], offset_x, offset_y, zoom_factor)
                        if (mouse_x - (x_2d - offset_x + (window_size[0]/2))) ** 2 + (mouse_y - (y_2d - offset_y + (window_size[1]/2))) ** 2 <= 3 ** 2:  # Check if within the circle of the star
                            selected_star_name = source_id
                            break  # Exit loop after finding a star

            # Handle key presses to toggle fullscreen mode
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_f:
                    is_fullscreen = not is_fullscreen
                    if is_fullscreen:
                        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                    else:
                        screen = pygame.display.set_mode(window_size, pygame.RESIZABLE)

                # Handle zooming
                if event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:  # Zoom in
                    zoom_factor += 10
                elif event.key == pygame.K_MINUS:  # Zoom out
                    zoom_factor = max(50, zoom_factor - 10)  # Prevent zooming out too much

                # Handle panning
                if event.key == pygame.K_UP:
                    offset_y += 1
                elif event.key == pygame.K_DOWN:
                    offset_y -= 1
                elif event.key == pygame.K_LEFT:
                    offset_x += 1
                elif event.key == pygame.K_RIGHT:
                    offset_x -= 1

            # Handle window resizing
            if event.type == pygame.VIDEORESIZE:
                window_size = event.size
                screen = pygame.display.set_mode(window_size, pygame.RESIZABLE)

        # Fill the screen with black color
        screen.fill(BLACK)

        # Draw Earth and stars
        draw_stars(screen, stars, window_size[0], window_size[1], offset_x, offset_y, zoom_factor)

        # Display the name of the selected star
        if selected_star_name:
            text_surface = font.render(str(selected_star_name), True, RED)  # Render the star name in red
            screen.blit(text_surface, (10, 10))  # Display at the top-left corner

        # Update the display
        pygame.display.flip()

    # Quit Pygame when the loop ends
    pygame.quit()

