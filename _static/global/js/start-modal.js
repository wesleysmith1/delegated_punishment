let startModalComponent = {
    components: {
        'grain-image-component': grainImageComponent,
    },
    props: {
        startObject: Object,
    },
    data: function() {
        return {

        }
    },
    methods: {
        open: function() {
            this.$refs.smodal.style.display = 'block';
        },
        close: function() {
            this.$refs.smodal.style.display = 'none';
        },
    },
    template:
        `
        <div ref="smodal" class="modal">
            <!--Modal content-->
            <div class="modal-content start-modal">
                <div class="start-modal-content">
                    <div v-if="startObject">
                        <h4 style="text-align:center;">Number of officer tokens determined for this round.</h4>
                        <p style="text-align: center;">Token summary</p>
                        <div class="list-group" style="width: 350px; margin: auto;">
                             <div v-if="startObject.your_tokens != null" class="list-group-item list-group-item-primary">
                                <div style="display: flex; justify-content: space-between;">
                                    <div>Your tokens:</div>
                                    <div>{{startObject.your_tokens}}</div>
                                </div>
                            </div>
                            <div v-if="startObject.your_tax != null" class="list-group-item list-group-item-primary">
                                <div style="display: flex; justify-content: space-between;">
                                    <div><strong>Your cost <grain-image-component :size=20></grain-image-component>:</strong></div>
                                    <div><strong>{{ startObject.your_tax | integerFilter }}</strong></div>
                                </div>
                            </div>
                            <div class="list-group-item list-group-item-primary">
                                <div style="display: flex; justify-content: space-between;">
                                    <div><strong>Total tokens:</strong></div>
                                    <div><strong>{{ startObject.defend_token_total | integerFilter }}</strong></div>
                                </div>
                            </div>
                            <div v-if="startObject.defend_token_cost != null" class="list-group-item list-group-item-primary">
                                <div style="display: flex; justify-content: space-between;">
                                    <div>Total cost <grain-image-component :size=20></grain-image-component>:</div>
                                    <div>{{ startObject.defend_token_cost }}</div>
                                </div>
                            </div>              
                        </div>
                    </div>
                </div>
            </div>
        </div>
        `
}