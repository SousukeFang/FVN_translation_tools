label start:
    # Scene: Opening
    "Narration with {i}style{/i} and [player_name]."
    eileen happy "Dialogue."
    eileen angry"Attribute touches quote."
    "Guest" "Explicit speaker."
    extend " Continued."
    show text "Title\nLine two" with dissolve
    menu:
        "First choice" if allowed:
            jump chosen
        "Second choice":
            call later

screen settings():
    label "Settings"
    text "Volume"
    textbutton "Back" action Return()
    tooltip "Return to the game"
    alt "Settings screen"

define translated_name = _("Display name")
$ renpy.notify("Saved")
$ renpy.input("Your name")

label multiline:
    '''A triple-quoted
narration.'''
