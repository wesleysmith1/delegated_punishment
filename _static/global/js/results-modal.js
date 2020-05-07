let resultsModalComponent = {
    props: {
        resultsObj: Object,
    },
    data: function() {
        return {

        }
    },
    methods: {
        openModal: function() {
            this.$refs.rmodal.style.display = 'block';
        }
    },
    template:
        `
        <div ref="rmodal" class="modal">

          <!-- Modal content -->
          <div class="modal-content results-modal">
            <div class="results-modal-content">
                <p>You obtained <strong>{{ balance | integerFilter}}</strong> grain</p>
            <!-- Modal content -->
            <div v-if="resultsObj" class="modal-content results-modal">
                <h4 style="text-align: center;">Round results</h4>
                
                <p class="card-title" style="text-align: center;">Earnings Summary</p>
                <div class="scrollable">
                    <table class="table table-floating table-debug">
                        <tbody>
                            <tr v-if="resultsObj.balance != null">
                                <td>After tax earnings <img src="https://i.imgur.com/BQXgE3F.png" alt="grain" style="height: 20px;"></td>
                                <td style="text-align: right;">{{ resultsObj.balance }}</td>
                            </tr>
                            <tr v-if="resultsObj['before_tax'] != null">
                                <td>Before tax earnings<img src="https://i.imgur.com/BQXgE3F.png" alt="grain" style="height: 20px;"></td>
                                <td style="text-align: right;">{{ resultsObj.before_tax }}</td>
                            </tr>
                            <tr v-if="resultsObj.your_tax != null">
                                <td scope="row">Taxes <img src="https://i.imgur.com/BQXgE3F.png" alt="grain" style="height: 20px;"></td>
                                <td style="text-align: right;">{{ resultsObj.your_tax }}</td>
                            </tr>    
                        </tbody>
                    </table>
                </div>
                <br>
                
                <p style="text-align: center;">Token summary</p>
                <div class="list-group" style="width: 350px; margin: auto;">
                     <div v-if="resultsObj.your_tokens != null" class="list-group-item list-group-item-primary">
                        <div style="display: flex; justify-content: space-between;">
                            <div><strong>Your tokens:</strong></div>
                            <div><strong>{{resultsObj.your_tokens}}</strong></div>
                        </div>
                    </div>
                    <div v-if="resultsObj.your_tax != null" class="list-group-item list-group-item-primary">
                        <div style="display: flex; justify-content: space-between;">
                            <div><strong>Your cost:</strong></div>
                            <div><strong>{{ resultsObj.your_tax }}</strong></div>
                        </div>
                    </div>
                    <div v-if="resultsObj.defend_token_cost != null" class="list-group-item list-group-item-primary">
                        <div style="display: flex; justify-content: space-between;">
                            <div>Total cost:</div>
                            <div>{{ resultsObj.defend_token_cost }}</div>
                        </div>
                    </div>              
                    <div class="list-group-item list-group-item-primary">
                        <div style="display: flex; justify-content: space-between;">
                            <div>Total tokens:</div>
                            <div>{{ resultsObj.defend_token_total }}</div>
                        </div>
                    </div>
                </div>
            </div>
            <div v-else>Results are loading...</div>
            </div>
                
        
        </div>
        `
}