let resultsModalComponent = {
    components: {
        'grain-image-component': grainImageComponent,
    },
    props: {
        resultsObj: Object,
        isOfficer: Boolean,
        income: Number, // needed to calculate officer breakdown
    },
    data: function() {
        return {

        }
    },
    methods: {
        openModal: function() {
            this.$refs.myModal.style.display = 'block';
        }
    },
    template:
        `
        <div ref="myModal" class="modal">

          <div class="modal-content results-modal">
            
            <div v-if="resultsObj" class="modal-content results-modal">
                <h4 style="text-align: center;">{{ resultsObj.title }}</h4>
                                
                <div class="list-group" style="width: 450px; margin: auto;">
                    
                    <div v-if="resultsObj.balance != null" class="list-group-item">
                        <div style="display: flex; justify-content: space-between;">
                            <div>Balance <grain-image-component :size=20></grain-image-component></div>
                            <div>{{ resultsObj.balance | integerFilter }}</div>
                        </div>
                    </div>      
    
                </div>
                <br>
                
                <template v-if="isOfficer">
                    <p style="text-align: center; margin-top: 15px;">Breakdown</p>
                    <div class="list-group" style="width: 450px; margin: auto;">
                        
                        <div v-if="resultsObj.fines != null" class="list-group-item list-group-item-primary">
                            <div style="display: flex; justify-content: space-between;">
                                <div>Amount earned ( <grain-image-component :size=20></grain-image-component>{{resultsObj.officer_bonus}} per civilian fined ):  </div>
                                <div><grain-image-component :size=20></grain-image-component>{{ resultsObj.fines * income }}</div>
                            </div>
                        </div>
                        <div v-if="resultsObj.reprimands != null" class="list-group-item list-group-item-primary">
                            <div style="display: flex; justify-content: space-between;">
                                <div>Amount lost ( <grain-image-component :size=20></grain-image-component>{{resultsObj.officer_reprimand_amount}} per reprimand ):</div>
                                <div><grain-image-component :size=20></grain-image-component>{{ resultsObj.reprimands * resultsObj.officer_reprimand_amount * -1 }}</div>
                            </div>
                        </div>   
                        
                    </div>
                </template>

            </div>
            
            
          </div>
        
        </div>
        `
}