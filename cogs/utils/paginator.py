import discord
    

class SimplePaginator(discord.ui.View):

    def __init__(self, ctx, source, *, page = 1, timeout = 180):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.source = source
        self.current_page = page
        self.message = None

    def _get_embed_from_page(self, page):
        return self.source.format_page(self, page)

    async def show_page(self, interaction, page_number):
        page = await self.source.get_page(page_number)
        self.current_page = page_number
        embed = self.source.format_page(self, page)
        await self._update_buttons()
        
        if interaction.response.is_done():
            if self.message:
                await self.message.edit(embed=embed, view=self)
        else:
            await interaction.response.edit_message(embed=embed, view=self)

    async def _update_buttons(self):
        self.back_button.disabled = self.current_page == 1
        self.next_button.disabled = self.current_page == self.source.get_max_pages() 

    @discord.ui.button(label='Back', style=discord.ButtonStyle.blurple)
    async def back_button(self, button, interaction):
        await self.show_page(interaction, self.current_page - 1)

    @discord.ui.button(label='Next', style=discord.ButtonStyle.blurple)
    async def next_button(self, button, interaction):
        await self.show_page(interaction, self.current_page + 1)

    async def start(self):
        await self.source._prepare_once()
        page = await self.source.get_page(self.current_page)
        embed = self.source.format_page(self, page)
        self.message = await self.ctx.send(embed=embed, view=self)
        await self._update_buttons()

        
