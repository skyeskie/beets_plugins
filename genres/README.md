# Genres plugin

Assist for managing genres both on and off the `genre` tag

This readme is mostly a roadmap currently.

## Fields

- main_genre - Single genre for track
- genres - all genre tags that apply to a set track
- album_genre - single genre tag for album
- album_genres - all genre tags that apply to any track on album

Then set main `genre` tag from one of the above options
Personally looking at album_genre

## Procedure

1. Backup existing genre
2. Pull/merge as many genre tags as possible
3. Shunt merged to genres
4. Move backup to genre
5. Collect/set album_genre and album_genres

Or for main import:

1. Pull/merge as many genre tags as possible

## Subcommands

### backup

Command to move all info in `genre` to `genre_bak`

### export

Command to export JSON of (genre, genres), keyed by (beets id, acoustid, path)

### import

Command to import JSON (format of export)

### restore

Command to move all info from `genre_back` to `genre`

### to_genres

Move contents of genre to genres (overwrite or merge)

## Set album_genre fields

### album_genre

- Pull from `genre` tag of all in album
- Multiple modes
    - Identical - set if all identical
    - Threshold - above set percentage (default 75%)
    - Tree - Use genres tree to walk up, finding most general tag containing all
- Various for non-match

### album_genres

- Merge genres tags of all 
