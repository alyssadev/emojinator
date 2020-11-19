emojinator
==========

A bot to manage emojis. All commands require the *user* to have Manage Emojis on the server; these don't bypass Discord permissions, they're time saving utility functions.

* `!emoji upload <custom emojis from another server>` - reuploads each provided emoji to the current server and says how many emoji slots are remaining
* `!emoji image <name>` - If an image is attached to the message, saves the given image as an emoji using the provided name
* `!emoji url <name> <url>` - specify an emoji name and image url to import. image must be smaller than 256kb
* `!emoji geturl <custom emoji> <another custom emoji> ...` - emoji urls will be listed to the user for further use
* `!emoji mashup` - get a random mashup from @emojimashupbot

[Invite](https://discord.com/oauth2/authorize?client_id=705796374532325416&scope=bot&permissions=1073743872)
