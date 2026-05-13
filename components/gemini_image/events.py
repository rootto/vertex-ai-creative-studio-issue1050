import mesop as me

def get_on_aspect_ratio_change(state_class):
    def on_aspect_ratio_change(e: me.SelectSelectionChangeEvent):
        """Updates the aspect ratio state."""
        me.state(state_class).aspect_ratio = e.value
    return on_aspect_ratio_change

def get_on_image_size_change(state_class):
    def on_image_size_change(e: me.SelectSelectionChangeEvent):
        """Updates the image size state."""
        me.state(state_class).image_size = e.value
    return on_image_size_change

def get_on_num_images_change(state_class):
    def on_num_images_change(e: me.SelectSelectionChangeEvent):
        """Updates the num_images_to_generate state."""
        me.state(state_class).num_images_to_generate = int(e.value)
    return on_num_images_change

def get_on_search_change(state_class):
    def on_search_change(e: me.CheckboxChangeEvent):
        """Updates the use_search state."""
        me.state(state_class).use_search = e.checked
    return on_search_change

def get_on_image_search_change(state_class):
    def on_image_search_change(e: me.CheckboxChangeEvent):
        """Updates the use_image_search state."""
        me.state(state_class).use_image_search = e.checked
    return on_image_search_change

def get_on_include_thoughts_change(state_class):
    def on_include_thoughts_change(e: me.CheckboxChangeEvent):
        """Updates the include_thoughts state."""
        me.state(state_class).include_thoughts = e.checked
    return on_include_thoughts_change

def get_on_thinking_level_change(state_class):
    def on_thinking_level_change(e: me.SelectSelectionChangeEvent):
        """Updates the thinking_level state."""
        me.state(state_class).thinking_level = e.value
    return on_thinking_level_change

def get_on_model_select(state_class):
    def on_model_select(e: me.WebEvent):
        """Updates the selected model."""
        state = me.state(state_class)
        
        # Depending on how the custom event is packed, it could be the raw string, or a dict.
        print(f"model_select raw event: key={e.key}, value={e.value}")
        val = e.value
        if isinstance(val, dict):
            val = val.get("value") or val.get("modelName")
            
        if not val:
            # Fallback to key if passed directly
            val = e.key
            
        if val:
            print(f"Setting selected_model to: {val}")
            state.selected_model = val
            # reset size and aspect ratio just to be safe if they are out of bounds
            state.image_size = "1K"
            state.aspect_ratio = "1:1"
        else:
            print("WARNING: model_select could not resolve a value from the event!")
    return on_model_select

def get_on_prompt_blur(state_class):
    def on_prompt_blur(e: me.InputBlurEvent):
        """Updates the prompt state when the input loses focus."""
        me.state(state_class).prompt = e.value
    return on_prompt_blur

def get_on_remove_image(state_class):
    def on_remove_image(e: me.ClickEvent):
        """Removes an uploaded image from the state."""
        state = me.state(state_class)
        index = int(e.key)
        if 0 <= index < len(state.uploaded_image_gcs_uris):
            state.uploaded_image_gcs_uris.pop(index)
            state.uploaded_image_display_urls.pop(index)
            if hasattr(state, 'image_descriptions') and 0 <= index < len(state.image_descriptions):
                state.image_descriptions.pop(index)
    return on_remove_image

def get_on_thumbnail_click(state_class):
    def on_thumbnail_click(e: me.ClickEvent):
        """Updates the selected image URL when a thumbnail is clicked."""
        me.state(state_class).selected_image_url = e.key
    return on_thumbnail_click
