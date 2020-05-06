let resultsModalComponent = {
    props: {
        balance: Number,
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

          <!-- Modal content -->
          <div class="modal-content results-modal">
            <div class="results-modal-content">
                <p>You obtained <strong>{{ balance }}</strong> grain</p>
            </div>
          </div>
        
        </div>
        `
}