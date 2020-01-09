
let harvestItemsComponent = {
    data: function () {
        return {
          items: ['plow', 'seed', 'water', 'harvest'], // todo: add none here for when nothing has been done or the user just dragged the harvest item successfully
          lastCompleted: null,
          currentStage: 0,
        }
    },
    mounted: function() {
      for (var i = 0; i < this.items.length; i++) {
        let that = this;
        Draggable.create("#" + this.items[i], {
          bounds: document.getElementById("harvestGame"),
          onDragEnd: function() {
            that.checkLocation(this)
          },
        });
      }
    },
    methods: {
      checkLocation: function(that, id) {
        let index = that.target.attributes.index.value;
        if( index==this.currentStage && that.hitTest(this.$refs.htarget, '100%') ){
          // $('#info').text('x: ' + targetX + ', y: ' + targetY );
          var tl = gsap.timeline({onComplete: this.updateHarvestStatus});
          tl.to(that.target, .5, {autoAlpha:0});
          tl.to(that.target, {x:0, y:0});
          // this.updateHarvestStatus()
        } else{
          gsap.to(that.target, 0.5, {x:0, y:0, ease: Back.easeOut});
        }
      },
      updateHarvestStatus() {
        this.currentStage++;
  
        //todo update api with currentStage
  
  
  
        if (this.currentStage == 4) {
          this.currentStage = 0; 
          gsap.to('#seed, #water, #plow, #harvest', 0.5, {autoAlpha:1});
        }
  
      }
    },
    template: `
  
      <div id="harvest-container" class="game">
        <div class="upper">
            <div class='harvest-items'>
              <div v-for='(i, index) in items' :id='i' :index='index' :ref='i' class='harvest-item'>
                {{i}}
                <img :src="'/static/global/images/' + i + '.png'" style="width: 50%; height: 50%"/>
              </div>
            </div>
        </div>
        <div class="lower" ref='htarget'> 
            <div class="harvest-complete-items">
              <div class="harvest-complete-container">
                <div class='harvest-complete-item' v-for='(i, index) in 3'>
                  <img v-if="currentStage > 0" :src="'/static/global/images/harvest' + (currentStage+1) + '.png'" style="width: 50%; height: 50%"/>
                </div>
              </div>
              <div class="harvest-complete-container">
                <div class='harvest-complete-item' v-for='(i, index) in 3'>
                  <img v-if="currentStage > 0" :src="'/static/global/images/harvest' + (currentStage+1) + '.png'" style="width: 50%; height: 50%"/>
                </div>
              </div>  
            </div>
        </div>
      </div>
    `
  }