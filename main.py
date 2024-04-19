import random
import math

import arcade
import os

from typing import cast
import arcade.gui

INITIAL_ASTEROID_COUNT = 3
SCALE = 0.5
BOUNDARY_PADDING = 300
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
SCREEN_TITLE = "Asteroid Smasher"
LEFT_BOUNDARY = -BOUNDARY_PADDING
RIGHT_BOUNDARY = WINDOW_WIDTH + BOUNDARY_PADDING
BOTTOM_BOUNDARY = -BOUNDARY_PADDING
TOP_BOUNDARY = WINDOW_HEIGHT + BOUNDARY_PADDING

MENU = "MENU"
GAME = "GAME"
HOW_TO = "HOW_TO"
GAME_OVER = "GAME_OVER"


class DirectionalSprite(arcade.Sprite):
    """ A sprite that automatically rotates to point in the direction
    it's moving."""

    def update(self):
        """Update the sprite's angle to point in the direction of its
        movement."""
        super().update()
        self.angle = math.degrees(math.atan2(self.change_y, self.change_x))


class ShipSprite(arcade.Sprite):
    """Represents the player's ship."""

    def __init__(self, filename, scale):
        """Initialize the ship sprite."""

        # Call the parent Sprite constructor
        super().__init__(filename, scale)

        # Info on where we are going.
        # Angle comes in automatically from the parent class.
        self.thrust = 0
        self.speed = 0
        self.max_speed = 4
        self.drag = 0.05
        self.respawning = 0

        # Mark that we are respawning.
        self.respawn()

    def respawn(self):
        """Reset position and attributes on respawn"""

        # If we are in the middle of respawning, this is non-zero.
        self.respawning = 1
        self.center_x = WINDOW_WIDTH / 2
        self.center_y = WINDOW_HEIGHT / 2
        self.angle = 0

    def update(self):
        """update ship position, speed, etc."""
        if self.respawning:
            self.respawning += 1
            self.alpha = self.respawning
            if self.respawning > 250:
                self.respawning = 0
                self.alpha = 255
        if self.speed > 0:
            self.speed -= self.drag
            if self.speed < 0:
                self.speed = 0

        if self.speed < 0:
            self.speed += self.drag
            if self.speed > 0:
                self.speed = 0

        self.speed += self.thrust
        if self.speed > self.max_speed:
            self.speed = self.max_speed
        if self.speed < -self.max_speed:
            self.speed = -self.max_speed

        self.change_x = -math.sin(math.radians(self.angle)) * self.speed
        self.change_y = math.cos(math.radians(self.angle)) * self.speed

        self.center_x += self.change_x
        self.center_y += self.change_y

        # If the ship goes off-screen, move it to the other side of the window
        if self.right < 0:
            self.left = WINDOW_WIDTH

        if self.left > WINDOW_WIDTH:
            self.right = 0

        if self.bottom < 0:
            self.top = WINDOW_HEIGHT

        if self.top > WINDOW_HEIGHT:
            self.bottom = 0

        super().update()


class AsteroidSprite(arcade.Sprite):
    """Represents an asteroid in the game."""

    def __init__(self, image_file_name, scale):
        super().__init__(image_file_name, scale=scale)
        self.size = 0

    def update(self):
        """Update asteroid position"""
        super().update()
        if self.center_x < LEFT_BOUNDARY:
            self.center_x = RIGHT_BOUNDARY
        if self.center_x > RIGHT_BOUNDARY:
            self.center_x = LEFT_BOUNDARY
        if self.center_y > TOP_BOUNDARY:
            self.center_y = BOTTOM_BOUNDARY
        if self.center_y < BOTTOM_BOUNDARY:
            self.center_y = TOP_BOUNDARY


class MyGame(arcade.Window):
    """Main application class"""

    def __init__(self):
        """Initialize game window"""
        super().__init__(WINDOW_WIDTH, WINDOW_HEIGHT, SCREEN_TITLE)

        self.game_over_displayed = None
        self.scene = MENU
        self.background = arcade.load_texture("Resources/Background/stars.png")

        self.uimanager = arcade.gui.UIManager()
        self.uimanager.enable()


        self.v_box = arcade.gui.UIBoxLayout(space_between=20)

        button_style = {
            "font_name": "Algerian",
            "font_size": 25,
            "font_color": (61, 212, 45),
            "bg_color": (0, 0, 0)
        }

        start_button = arcade.gui.UIFlatButton(text="New Game", width=300, style=button_style)

        start_button.on_click = self.on_click_start

        self.uimanager.add(
            arcade.gui.UIAnchorWidget(
                anchor_x='center_x',
                anchor_y='center_y',
                child=start_button
            )
        )

        how_to_button = arcade.gui.UIFlatButton(text="How To Play", width=300, style=button_style)

        how_to_button.on_click = self.how_to_play

        self.uimanager.add(
            arcade.gui.UIAnchorWidget(
                anchor_x='center_x',
                anchor_y='center_y',
                child=how_to_button
            )
        )

        self.v_box.add(start_button)
        self.v_box.add(how_to_button)

        self.uimanager.add(
            arcade.gui.UIAnchorWidget(
                anchor_x='center_x',
                anchor_y='center_y',
                child=self.v_box
            )
        )

        self.how_to_manager = arcade.gui.UIManager()
        self.how_to_manager.enable()
        return_button_style = {
            "font_name": "Algerian",
            "font_size": 25,
            "font_color": (61, 212, 45),
            "bg_color": (0, 0, 0)
        }
        back_button = arcade.gui.UIFlatButton(text="Back to Menu", width=300, style=return_button_style)

        back_button.on_click = self.return_to_menu

        self.how_to_manager.add(
            arcade.gui.UIAnchorWidget(
                anchor_x='left',
                anchor_y='bottom',
                child=back_button
            )
        )

        # Set the working directory (where we expect to find files) to the same
        # directory this .py file is in. You can leave this out of your own
        # code, but it is needed to easily run the examples using "python -m"
        # as mentioned at the top of this program.
        file_path = os.path.dirname(os.path.abspath(__file__))
        os.chdir(file_path)

        self.frame_count = 0

        self.game_over = False

        # Sprite lists
        self.player_sprite_list = arcade.SpriteList()
        self.asteroid_list = arcade.SpriteList()
        self.bullet_list = arcade.SpriteList()
        self.ship_life_list = arcade.SpriteList()

        # Set up the player
        self.score = 0
        self.player_sprite = None
        self.lives = 3

        # Sounds
        self.laser_sound = arcade.load_sound(":resources:sounds/hurt5.wav")
        self.hit_sound1 = arcade.load_sound(":resources:sounds/explosion1.wav")
        self.hit_sound2 = arcade.load_sound(":resources:sounds/explosion2.wav")
        self.hit_sound3 = arcade.load_sound(":resources:sounds/hit1.wav")
        self.hit_sound4 = arcade.load_sound(":resources:sounds/hit2.wav")

    def on_click_start(self, event):
        self.start_new_game()
        self.scene = GAME
        self.uimanager.disable()
        print("Start:", event)

    def how_to_play(self, event):
        self.start_new_game()
        self.scene = HOW_TO
        self.uimanager.disable()
        self.how_to_manager.enable()
        print("Start:", event)

    def return_to_menu(self, event):
        self.start_new_game()
        self.scene = MENU
        self.how_to_manager.disable()
        self.uimanager.enable()
        print("Start:", event)

    def start_new_game(self):
        """Begin new game"""

        self.background = arcade.load_texture("Resources/Background/stars.png")
        self.frame_count = 0
        self.game_over = False

        # Sprite lists
        self.player_sprite_list = arcade.SpriteList()
        self.asteroid_list = arcade.SpriteList()
        self.bullet_list = arcade.SpriteList()
        self.ship_life_list = arcade.SpriteList()

        # Set up the player
        self.score = 0
        self.player_sprite = ShipSprite(":resources:images/space_shooter/"
                                        "playerShip1_orange.png",
                                        SCALE)
        self.player_sprite_list.append(self.player_sprite)
        self.lives = 3

        # Set up the little icons that represent the player lives.
        cur_pos = 10
        for i in range(self.lives):
            life = arcade.Sprite(":resources:images/space_shooter/"
                                 "playerLife1_orange.png",
                                 SCALE)
            life.center_x = cur_pos + life.width
            life.center_y = life.height
            cur_pos += life.width
            self.ship_life_list.append(life)

        # Make the asteroids
        image_list = (":resources:images/space_shooter/meteorGrey_big1.png",
                      ":resources:images/space_shooter/meteorGrey_big2.png",
                      ":resources:images/space_shooter/meteorGrey_big3.png",
                      ":resources:images/space_shooter/meteorGrey_big4.png")
        for i in range(INITIAL_ASTEROID_COUNT):
            image_no = random.randrange(4)
            asteroids = AsteroidSprite(image_list[image_no], SCALE)
            asteroids.guid = "Asteroid"

            asteroids.center_y = random.randrange(BOTTOM_BOUNDARY, TOP_BOUNDARY)
            asteroids.center_x = random.randrange(LEFT_BOUNDARY, RIGHT_BOUNDARY)

            asteroids.change_x = random.random() * 2 - 1
            asteroids.change_y = random.random() * 2 - 1

            asteroids.change_angle = (random.random() - 0.5) * 2
            asteroids.size = 4
            self.asteroid_list.append(asteroids)

    def on_draw(self):

        """Render screen"""
        self.clear()
        arcade.start_render()

        if self.scene == MENU:
            arcade.draw_lrwh_rectangle_textured(0, 0,
                                                WINDOW_WIDTH, WINDOW_HEIGHT,
                                                self.background)

            self.uimanager.draw()

        elif self.scene == GAME:

            arcade.draw_lrwh_rectangle_textured(0, 0,
                                                WINDOW_WIDTH, WINDOW_HEIGHT,
                                                self.background)

            self.asteroid_list.draw()
            self.ship_life_list.draw()
            self.bullet_list.draw()
            self.player_sprite_list.draw()

            output = f"Score: {self.score}"
            arcade.draw_text(output, 10, 70, arcade.color.WHITE, 13)

            output = f"Asteroid Count: {len(self.asteroid_list)}"
            arcade.draw_text(output, 10, 50, arcade.color.WHITE, 13)

        elif self.scene == HOW_TO:

            arcade.draw_lrwh_rectangle_textured(0, 0,
                                                WINDOW_WIDTH, WINDOW_HEIGHT,
                                                arcade.load_texture("Resources/Background/howto.png"))

            self.how_to_manager.draw()

        elif self.scene == GAME_OVER:

            arcade.draw_text('Game Over', 400, 300, (61, 212, 45), 30,
                             400, 'center', "Algerian", False, False,
                             'center', 'center')

    def on_key_press(self, symbol, modifiers):
        """Handle Key press events"""
        # Shoot if the player hit the space bar and we aren't respawning.
        if not self.player_sprite.respawning and symbol == arcade.key.SPACE:
            bullet_sprite = DirectionalSprite(":resources:images/space_shooter/"
                                              "laserBlue01.png",
                                              SCALE)
            bullet_sprite.guid = "Bullet"

            bullet_speed = 13
            bullet_sprite.change_y = \
                math.cos(math.radians(self.player_sprite.angle)) * bullet_speed
            bullet_sprite.change_x = \
                -math.sin(math.radians(self.player_sprite.angle)) \
                * bullet_speed

            bullet_sprite.center_x = self.player_sprite.center_x
            bullet_sprite.center_y = self.player_sprite.center_y
            bullet_sprite.update()

            self.bullet_list.append(bullet_sprite)

            arcade.play_sound(self.laser_sound)

        if symbol == arcade.key.LEFT:
            self.player_sprite.change_angle = 3
        elif symbol == arcade.key.RIGHT:
            self.player_sprite.change_angle = -3
        elif symbol == arcade.key.UP:
            self.player_sprite.thrust = 0.15
        elif symbol == arcade.key.DOWN:
            self.player_sprite.thrust = -.2

    def on_key_release(self, symbol, modifiers):
        """Handle key release events"""
        if symbol == arcade.key.LEFT:
            self.player_sprite.change_angle = 0
        elif symbol == arcade.key.RIGHT:
            self.player_sprite.change_angle = 0
        elif symbol == arcade.key.UP:
            self.player_sprite.thrust = 0
        elif symbol == arcade.key.DOWN:
            self.player_sprite.thrust = 0

    def split_asteroid(self, asteroid: AsteroidSprite):
        """Split asteroids on hit"""
        x = asteroid.center_x
        y = asteroid.center_y
        self.score += 1

        if asteroid.size == 4:
            for i in range(3):
                image_no = random.randrange(2)
                image_list = [":resources:images/space_shooter/meteorGrey_med1.png",
                              ":resources:images/space_shooter/meteorGrey_med2.png"]

                asteroid_sprite = AsteroidSprite(image_list[image_no],
                                                 SCALE * 1.5)

                asteroid_sprite.center_y = y
                asteroid_sprite.center_x = x

                asteroid_sprite.change_x = random.random() * 2.5 - 1.25
                asteroid_sprite.change_y = random.random() * 2.5 - 1.25

                asteroid_sprite.change_angle = (random.random() - 0.5) * 2
                asteroid_sprite.size = 3

                self.asteroid_list.append(asteroid_sprite)
                self.hit_sound1.play()

        elif asteroid.size == 3:
            for i in range(3):
                image_no = random.randrange(2)
                image_list = [":resources:images/space_shooter/meteorGrey_small1.png",
                              ":resources:images/space_shooter/meteorGrey_small2.png"]

                asteroid_sprite = AsteroidSprite(image_list[image_no],
                                                 SCALE * 1.5)

                asteroid_sprite.center_y = y
                asteroid_sprite.center_x = x

                asteroid_sprite.change_x = random.random() * 3 - 1.5
                asteroid_sprite.change_y = random.random() * 3 - 1.5

                asteroid_sprite.change_angle = (random.random() - 0.5) * 2
                asteroid_sprite.size = 2

                self.asteroid_list.append(asteroid_sprite)
                self.hit_sound2.play()

        elif asteroid.size == 2:
            for i in range(3):
                image_no = random.randrange(2)
                image_list = [":resources:images/space_shooter/meteorGrey_tiny1.png",
                              ":resources:images/space_shooter/meteorGrey_tiny2.png"]

                asteroid_sprite = AsteroidSprite(image_list[image_no],
                                                 SCALE * 1.5)

                asteroid_sprite.center_y = y
                asteroid_sprite.center_x = x

                asteroid_sprite.change_x = random.random() * 3.5 - 1.75
                asteroid_sprite.change_y = random.random() * 3.5 - 1.75

                asteroid_sprite.change_angle = (random.random() - 0.5) * 2
                asteroid_sprite.size = 1

                self.asteroid_list.append(asteroid_sprite)
                self.hit_sound3.play()

        elif asteroid.size == 1:
            self.hit_sound4.play()

    def on_update(self, x):

        """Update game state"""
        self.frame_count += 1

        self.total_time += x

        if not self.game_over:
            self.asteroid_list.update()
            self.bullet_list.update()
            self.player_sprite_list.update()

            for bullet in self.bullet_list:
                asteroids = arcade.check_for_collision_with_list(bullet,
                                                                 self.asteroid_list)

                for asteroid in asteroids:
                    # expected AsteroidSprite, got Sprite instead
                    self.split_asteroid(cast(AsteroidSprite, asteroid))
                    asteroid.remove_from_sprite_lists()
                    bullet.remove_from_sprite_lists()

                # Remove bullet if it goes off-screen
                size = max(bullet.width, bullet.height)
                if bullet.center_x < 0 - size:
                    bullet.remove_from_sprite_lists()
                if bullet.center_x > WINDOW_WIDTH + size:
                    bullet.remove_from_sprite_lists()
                if bullet.center_y < 0 - size:
                    bullet.remove_from_sprite_lists()
                if bullet.center_y > WINDOW_HEIGHT + size:
                    bullet.remove_from_sprite_lists()

            if not self.player_sprite.respawning:
                asteroids = arcade.check_for_collision_with_list(self.player_sprite,
                                                                 self.asteroid_list)
                if len(asteroids) > 0:
                    if self.lives > 0:
                        self.lives -= 1
                        self.player_sprite.respawn()
                        self.split_asteroid(cast(AsteroidSprite, asteroids[0]))
                        asteroids[0].remove_from_sprite_lists()
                        self.ship_life_list.pop().remove_from_sprite_lists()
                        print("Crash")
                    else:
                        self.game_over = True
                        self.frame_count = 0
                        self.game_over_screen()
        elif self.scene == GAME_OVER and self.game_over_displayed:

            self.frame_count += 1
            if self.frame_count >= 300:
                self.frame_count = 0
                self.scene = MENU
                self.start_new_game()

    def game_over_screen(self):
        self.scene = GAME_OVER
        self.game_over_displayed = True


def main():
    """Main function to start game"""
    window = MyGame()
    window.start_new_game()
    arcade.run()


if __name__ == "__main__":
    main()
