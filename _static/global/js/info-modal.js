let infoModalComponent = {
    components: {
        'grain-image-component': grainImageComponent,
    },
    props: {
        startObject: Object,
        isOfficer: Boolean,
        groupPlayerId: Number,
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
        incomeItem(i) {
            console.log('here is the index')
            if (this.groupPlayerId === i + 2) {
                return {fontWeight: 'bold'}
            } else {
                return {}
            }
        }

    },
    computed: {
        officerItem() {
            return this.isOfficer ? {fontWeight: 'bold'} : {}
        },
        civilianItem() {
            return this.isOfficer ? {} : {fontWeight: 'bold'}
        },
    },
    template:
        `
        <div ref="smodal" class="modal">
            <!--Modal content-->
            <div class="modal-content start-modal">
                <div class="start-modal-content">
                    <div v-if="startObject">
                        <h4 style="text-align:center;">Round information</h4>
                        <br>
                        <!--<p style="text-align: center;">Token summary</p>-->
                                        
                        <div class="list-group" style="width: 350px; margin: auto;">
                             <div class="list-group-item">
                                <div style="display: flex; justify-content: space-between;">
                                    <div>Officer bonus <grain-image-component :size=20></grain-image-component>:</div>
                                    <div :style=officerItem>{{startObject.officer_bonus}}</div>
                                </div>
                            </div>
                            <div class="list-group-item">
                                <div style="display: flex; justify-content: space-between;">
                                    <div>Officer reprimand <grain-image-component :size=20></grain-image-component>:</div>
                                    <div :style="officerItem">{{ startObject.officer_reprimand }}</div>
                                </div>
                            </div>
                            <div class="list-group-item">
                                <div style="display: flex; justify-content: space-between;">
                                    <div>Civilian fine if punished <grain-image-component :size=20></grain-image-component>:</div>
                                    <div :style="civilianItem">{{ startObject.civilian_fine }}</div>
                                </div>
                            </div>
                            <div class="list-group-item">
                                <div style="display: flex; justify-content: space-between;">
                                    <div>Civilian steal rate <grain-image-component :size=20></grain-image-component>:</div>
                                    <div :style="civilianItem">{{ startObject.steal_rate }}</div>
                                </div>
                            </div>
                            <div class="list-group-item">
                                <div style="display: flex; justify-content: space-between;">
                                    <div>Civilian harvest rates <grain-image-component :size=20></grain-image-component>:</div>
                                    <div>
                                        <span v-for="(income, index) in startObject.civilian_incomes" v-bind:style="incomeItem(index)">
                                            {{ income }}
                                        </span>
                                    </div>
                                </div>
                            </div>        
                        </div>
                    </div>
                </div>
            </div>
        </div>
        `
}